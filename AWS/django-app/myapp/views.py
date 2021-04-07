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
        variables = RequestContext(request, {'items':items})
        return render_to_response('dashboard.html', variables)
    else:
        variables = RequestContext(request, {})
        return render_to_response('login.html', variables)

def download(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rawdata.csv"'
    
    writer = csv.writer(response)
    now=int(time.time())
    timestampold=now-86400
    response2 = table.scan(
        FilterExpression=Attr('timestamp').gt(timestampold)
    )
    items = response2['Items']
    writer.writerow(['Station ID', 'Timestamp', 'Latitude', 'Longitude', 'Ambient Temperature', 'Ambient Humidity', 'Snow Temperature', 'Snow Depth'])
    for i in range(len(items)):
        writer.writerow([items[i]['stationID'], items[i]['timestamp'], items[i]['data']['latitude'], items[i]['data']['longitude'], items[i]['data']['amb_temp'], items[i]['data']['amb_hum'], items[i]['data']['snow_temp'], items[i]['data']['snow_depth']])
    return response

def filter_data(request,asset_filter):
    now=int(time.time())
    timestampold=now-86400

    if asset_filter=='all':
        stationID=''
        response = table.scan(
            FilterExpression=Attr('timestamp').gt(timestampold)
        )
    elif asset_filter=='ST102':
        stationID='ST102'
        response = table.scan(
            FilterExpression=Key('stationID').eq(stationID) & Attr('timestamp').gt(timestampold)
        )
    elif asset_filter=='ST105':
        stationID='ST105'
        response = table.scan(
            FilterExpression=Key('stationID').eq(stationID) & Attr('timestamp').gt(timestampold)
        )
    
    items = response['Items']
    variables = RequestContext(request, {'items':items})
    return render_to_response('dashboard.html',variables)


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
    print(request.GET)
    print(request.POST)
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
            try:
                #Provide the contents of the email.
                response = ses.send_email(
                    Destination={
                        'ToAddresses': [RECEIVER],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Data': 'Confirm your email at http://ec2-3-80-50-95.compute-1.amazonaws.com:5000/confirm/' + str(token),
                            },
                        },
                        'Subject': {
                            'Data': 'Photo Gallery Email Confirmation'
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
            return render_to_response('confirmemail.html')
        variables = RequestContext(request, {})
        return render_to_response('login.html', variables)
    else:
        variables = RequestContext(request, {})
        return render_to_response('signup.html', variables)

def login(request):
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            existing_email = users_table.scan(FilterExpression=Attr('email').eq(email))
            matching_email = existing_email['Items']
            if existing_email is None:
                return redirect('/')
            elif (bcrypt.hashpw(password.encode('utf-8'), matching_email[0]['password'].value) == matching_email[0]['password'].value) and matching_email[0]['verified'] == "yes":
                serializer = URLSafeTimedSerializer('some_secret_key')
                session['email'] = serializer.dumps(matching_email[0]['email'], salt="some-secret-salt-for-confirmation")
            return redirect('/')
        except Exception as e:
            print(e)
            return redirect('/')
    else:
        variables = RequestContext(request, {})
        return render_to_response('login.html', variables)

def dashboard_home(request):    
    variables = RequestContext(request, {})
    return render_to_response('dashboard.html', variables)

def signup(request):
    variables = RequestContext(request, {})
    return render_to_response('signup.html', variables)

def forgot(request):
    return render_to_response('forgotpassword.html')