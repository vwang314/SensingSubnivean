from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseBadRequest
from django.shortcuts import redirect
from django.conf import settings
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group, Permission, User
from django.db.models import Count, Min, Sum, Avg
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import sys, os
import time
from django.shortcuts import render
import csv
import boto3
from django.utils import timezone
from boto3.dynamodb.conditions import Key, Attr
import matplotlib.pyplot as plt
import io, base64
import bcrypt
import uuid
from itsdangerous import URLSafeTimedSerializer
from django.template.context_processors import csrf

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table('SubniveanData')
users_table = dynamodb.Table('SubniveanUser')

def check_login_session(request):
    value = request.session.get('email','no_email_provided')
    if value != 'no_email_provided':
        try:
            serializer = URLSafeTimedSerializer('some_secret_key')
            decode = serializer.loads(
                request.session['email'],
                salt = 'some-secret-salt-for-confirmation',
                #max_age = 300
            )
            return True
        except Exception as e:
            del request.session['email']
            print('Token Expired')
            return False
    else:
        return False

def home_page(request):
    if check_login_session(request):
        #ts=datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        #timestampold=str(ts.strftime("%Y-%m-%dT:%H:%M:%S"))
        now=int(time.time())
        timestampold=now-86400

        response = table.scan(
            FilterExpression=Attr('timestamp').gt(timestampold)
        )

        items = response['Items']
        username = request.session['username']
        name = request.session['name']
        variables = RequestContext(request, {'items':items, 'name':name, 'username':username})
        return render_to_response('dashboard.html', variables)
    else:
        return redirect('/login')

def download(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subniveandata.csv"'
        
        writer = csv.writer(response)
        now=int(time.time())
        timestampold=now-86400
        response2 = table.scan(
            FilterExpression=Attr('timestamp').gt(timestampold)
        )
        items = response2['Items']
        writer.writerow(['Station ID', 'Timestamp', 'Ambient Temperature', 'Ambient Humidity', 'Snow Temperature', 'Snow Depth'])
        for i in range(len(items)):
            writer.writerow([items[i]['stationID'], items[i]['timestamp'], items[i]['data']['ambTemp'], items[i]['data']['ambHum'], items[i]['data']['snowTemp'], items[i]['data']['snowDepth']])
        return response
    except Exception as e:
        print(e)

def filter_data_time(request,time_filter):
    timestampold=''
    now=int(time.time())
    if time_filter=='1':
        timestampold=now - 60
    elif time_filter=='2':
        timestampold=now - 900
    elif time_filter=='3':
        timestampold=now - 3600
    elif time_filter=='4':
        timestampold=now - 21600
    elif time_filter=='5':
        timestampold=now - 43200
    elif time_filter=='6':
        timestampold=now - 86400
            
    print(timestampold)
    response = table.scan(
            FilterExpression=Attr('timestamp').gt(timestampold)
        )
    items = response['Items']
    variables = RequestContext(request, {'items':items})
    return render_to_response('dashboard.html',variables)

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        existing_emails = users_table.scan(FilterExpression=Attr('email').eq(email))
        matching_emails = existing_emails['Items']
        if (len(matching_emails) == 0) and (password == password1):
            userID = uuid.uuid4()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users_table.put_item(
                Item={
                    "userID": str(userID),
                    "username": username,
                    "name": name,
                    "email": email,
                    "password": hashed_password,
                    "verified": "no"
                }
            )
            serializer = URLSafeTimedSerializer('some_secret_key')
            token = serializer.dumps(email, salt='some-secret-salt-for-confirmation')
            ses = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
            SENDER = 'vwang314@gatech.edu'
            RECEIVER = email
            print(token)
            try:
                #Provide the contents of the email.
                response = ses.send_email(
                    Destination={
                        'ToAddresses': [RECEIVER],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Data': 'Confirm your email at http://ec2-54-175-15-136.compute-1.amazonaws.com:8000/confirm/?p=' + str(token),
                            },
                        },
                        'Subject': {
                            'Data': 'Subnivean Data Email Confirmation'
                        },
                    },
                    Source=SENDER
                )
            # Display an error if something goes wrong.
            except ClientError as e:
                print(e.response['Error']['Message'])
            else:
                print("Email sent! Message ID:"),
                print(response['MessageId']),
                print(token),
            return redirect('/confirmemail')
        return redirect('/login')
    else:
        variables = RequestContext(request, {})
        return render_to_response('signup.html', variables)

def confirm(request):
    token = request.GET['p']
    print(token)
    try:
        serializer = URLSafeTimedSerializer('some_secret_key')
        email = serializer.loads(
            str(token),
            salt = 'some-secret-salt-for-confirmation'
        )
        users_table.update_item(
            Key={
                'email': email
            },
            UpdateExpression = "set verified=:v",
            ExpressionAttributeValues={ 
                ':v': "yes" 
            }
        )
        return redirect('/login')
    except Exception as e:
        print('error confirming email')
        return redirect('/signup')

def login(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            existing_username = users_table.scan(FilterExpression=Attr('username').eq(username))
            matching_username = existing_username['Items']
            if existing_username is None:
                return redirect('/')
            elif (bcrypt.hashpw(password.encode('utf-8'), matching_username[0]['password'].value) == matching_username[0]['password'].value) and matching_username[0]['verified'] == "yes":
                serializer = URLSafeTimedSerializer('some_secret_key')
                request.session['email'] = serializer.dumps(matching_username[0]['email'], salt="some-secret-salt-for-confirmation")
                request.session['username'] = matching_username[0]['username']
                request.session['name'] = matching_username[0]['name']
            return redirect('/')
        except Exception as e:
            print(e)
            return redirect('/')
    else:
        variables = RequestContext(request, {})
        return render_to_response('login.html', variables)

def logout(request):
    try:
        del request.session['email']
        return redirect('/')
    except Exception as e:
        print(e)
        return redirect('/login')

def dashboard_home(request):    
    variables = RequestContext(request, {})
    return render_to_response('dashboard.html', variables)

def confirmemail(request):
    variables = RequestContext(request, {})
    return render_to_response('confirmemail.html', variables)

def forgot(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        existing_emails = users_table.scan(FilterExpression=Attr('email').eq(email))
        matching_emails = existing_emails['Items']
        if (len(matching_emails) == 1):
            serializer = URLSafeTimedSerializer('some_secret_key')
            token = serializer.dumps(email, salt='some-secret-salt-for-confirmation')
            ses = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
            SENDER = 'vwang314@gatech.edu'
            RECEIVER = email
            print(token)
            try:
                #Provide the contents of the email.
                response = ses.send_email(
                    Destination={
                        'ToAddresses': [RECEIVER],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Data': 'Reset your password at http://ec2-54-175-15-136.compute-1.amazonaws.com:8000/np/  \n Use the confirmation key:   ' + str(token),
                            },
                        },
                        'Subject': {
                            'Data': 'Subnivean Data Password Reset'
                        },
                    },
                    Source=SENDER
                )
            # Display an error if something goes wrong.
            except ClientError as e:
                print(e.response['Error']['Message'])
            else:
                print("Email sent! Message ID:"),
                print(response['MessageId']),
                print(token),
        return redirect('/login')
    else:
        variables = RequestContext(request, {})
        return render_to_response('forgotpassword.html', variables)
    
def newpassword(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        if(password == password1):
            try:
                serializer = URLSafeTimedSerializer('some_secret_key')
                email = serializer.loads(
                    str(token),
                    salt = 'some-secret-salt-for-confirmation'
                )
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                users_table.update_item(
                    Key={
                        'email': email
                    },
                    UpdateExpression = "SET password=:p",
                    ExpressionAttributeValues={ 
                        ':p': hashed_password 
                    }
                )
                return redirect('/login')
            except Exception as e:
                print('error resetting password')
                print(e)
                return redirect('/np/')
        else:
            return redirect('/np/')
    else:
        variables = RequestContext(request, {})
        return render_to_response('newpassword.html', variables)

def changepassword(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        if(password == password1):
            try:
                serializer = URLSafeTimedSerializer('some_secret_key')
                email = serializer.loads(request.session['email'], salt="some-secret-salt-for-confirmation")
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                users_table.update_item(
                    Key={
                        'email': email
                    },
                    UpdateExpression = "SET password=:p",
                    ExpressionAttributeValues={ 
                        ':p': hashed_password 
                    }
                )
                return redirect('/')
            except Exception as e:
                print('error changing password')
                print(e)
                return redirect('/cp/')
        else:
            return redirect('/cp/')
    else:
        variables = RequestContext(request, {})
        return render_to_response('changepassword.html', variables)