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
    #if check_login_session(request):
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
    #else:
    #    return render_to_response('login.html')

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

def dashboard_home(request):    
    variables = RequestContext(request, {})
    return render_to_response('dashboard.html', variables)


