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
# import pwd
# import grp
# import json, simplejson
# from datetime import datetime, date, timedelta
# from dateutil import relativedelta
import time
from django.shortcuts import render
import csv
# import requests
# import operator
# from lxml.html import fromstring
# import glob
# import zipfile
# import random
# import re
# import sha
# from .models import *
import boto3
from django.utils import timezone
# import json
from boto3.dynamodb.conditions import Key, Attr
# import datetime
# from dateutil.tz import tzoffset
#import matplotlib
import matplotlib.pyplot as plt
#matplotlib.use('Agg')
import io, base64

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table('AirQualityData')
table_output = dynamodb.Table('AirQualityDataOutput')

def home_page(request):
    #ts=datetime.datetime.utcnow() - datetime.timedelta(hours=12)
    #timestampold=str(ts.strftime("%Y-%m-%dT:%H:%M:%S"))
    now=int(time.time())
    timestampold=now-86400

    response = table_output.scan(
        FilterExpression=Attr('timestamp').gt(timestampold)
    )

    items = response['Items']
    variables = RequestContext(request, {'items':items})
    return render_to_response('aqi-computed.html', variables)


def raw_data_page(request):
    #ts=datetime.datetime.utcnow() - datetime.timedelta(hours=12)
    #timestampold=str(ts.strftime("%Y-%m-%dT:%H:%M:%S"))
    now=int(time.time())
    timestampold=now-86400

    response = table.scan(
        FilterExpression=Attr('timestamp').gt(timestampold)
    )

    items = response['Items']
    variables = RequestContext(request, {'items':items})
    return render_to_response('aqi-dashboard.html', variables)

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
    writer.writerow(['Station ID', 'Timestamp', 'Latitude', 'Longitude', 'PM2.5', 'PM10', 'CO', 'SO2'])
    for i in range(len(items)):
        writer.writerow([items[i]['stationID'], items[i]['timestamp'], items[i]['data']['latitude'], items[i]['data']['longitude'], items[i]['data']['pm2_5'], items[i]['data']['pm10'], items[i]['data']['co'], items[i]['data']['so2']])
    return response

def analytics(request):
    timestamp = [[],[]]
    latitude = [[],[]]
    longitude = [[],[]]
    pm2_5 = [[],[]]
    pm10 = [[],[]]
    co = [[],[]]
    so2 = [[],[]]
    with open(os.getcwd()+'/rawdata.csv','r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            if(row[0] == 'ST102'):
                timestamp[0].append(int(row[1]))
                pm2_5[0].append(float(row[4]))
                pm10[0].append(float(row[5]))
                co[0].append(float(row[6]))
                so2[0].append(float(row[7]))
            elif(row[0] == 'ST105'):
                timestamp[1].append(int(row[1]))
                pm2_5[1].append(float(row[4]))
                pm10[1].append(float(row[5]))
                co[1].append(float(row[6]))
                so2[1].append(float(row[7]))


    fig, ax = plt.subplots(4, 2, figsize=(18,22))
    ax[0,0].plot(timestamp[0], pm2_5[0])
    ax[0,0].set_title('ST102 PM2.5')
    ax[0,1].plot(timestamp[0], pm10[0])
    ax[0,1].set_title('ST102 PM10')
    ax[1,0].plot(timestamp[0], co[0])
    ax[1,0].set_title('ST102 CO')
    ax[1,1].plot(timestamp[0], so2[0])
    ax[1,1].set_title('ST102 SO2')
    ax[2,0].plot(timestamp[1], pm2_5[1])
    ax[2,0].set_title('ST105 PM2.5')
    ax[2,1].plot(timestamp[1], pm10[1])
    ax[2,1].set_title('ST105 PM10')
    ax[3,0].plot(timestamp[1], co[1])
    ax[3,0].set_title('ST105 CO')
    ax[3,1].plot(timestamp[1], so2[1])
    ax[3,1].set_title('ST105 SO2')
    for axs in ax.flat:
        axs.xaxis.set_major_locator(plt.MaxNLocator(5))
        axs.yaxis.set_major_locator(plt.MaxNLocator(10))
        axs.set(xlabel='Time')
    plt.subplots_adjust(hspace=0.8)

    flike = io.BytesIO()
    fig.savefig(flike)
    b64 = base64.b64encode(flike.getvalue()).decode()
    variables = RequestContext(request, {'chart':b64})
    return render_to_response('analytics.html', variables)

def filter_data(request,asset_filter):
    now=int(time.time())
    timestampold=now-86400

    if asset_filter=='all':
        stationID=''
        response = table_output.scan(
            FilterExpression=Attr('timestamp').gt(timestampold)
        )
    elif asset_filter=='ST102':
        stationID='ST102'
        response = table_output.scan(
            FilterExpression=Key('stationID').eq(stationID) & Attr('timestamp').gt(timestampold)
        )
    elif asset_filter=='ST105':
        stationID='ST105'
        response = table_output.scan(
            FilterExpression=Key('stationID').eq(stationID) & Attr('timestamp').gt(timestampold)
        )
    
    items = response['Items']
    variables = RequestContext(request, {'items':items})
    return render_to_response('aqi-computed.html',variables)


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
    response = table_output.scan(
            FilterExpression=Attr('timestamp').gt(timestampold)
        )
    items = response['Items']
    variables = RequestContext(request, {'items':items})
    return render_to_response('aqi-computed.html',variables)

def filter_raw_data(request,asset_filter):
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
    return render_to_response('aqi-dashboard.html',variables)


def filter_raw_data_time(request,time_filter):
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
    return render_to_response('aqi-dashboard.html',variables)    

def dashboard_home(request):    
    variables = RequestContext(request, {})
    return render_to_response('aqi-dashboard.html', variables)


