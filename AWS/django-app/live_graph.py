import sys, os
import time
import csv
import boto3
from boto3.dynamodb.conditions import Key, Attr
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
    
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table('AirQualityData')



def animate(i):
    timestamp = [[],[]]
    pm2_5 = [[],[]]
    pm10 = [[],[]]
    co = [[],[]]
    so2 = [[],[]]
    now=int(time.time())
    timestampold=now-86400
    response = table.scan(
        FilterExpression=Attr('timestamp').gt(timestampold)
    )
    data = response['Items']
    for i in range(len(data)):
        if(data[i]['stationID'] == 'ST102'):
            timestamp[0].append(int(data[i]['timestamp']))
            pm2_5[0].append(float(data[i]['data']['pm2_5']))
            pm10[0].append(float(data[i]['data']['pm10']))
            co[0].append(float(data[i]['data']['co']))
            so2[0].append(float(data[i]['data']['so2']))
        elif(data[i]['stationID'] == 'ST105'):
            timestamp[1].append(int(data[i]['timestamp']))
            pm2_5[1].append(float(data[i]['data']['pm2_5']))
            pm10[1].append(float(data[i]['data']['pm10']))
            co[1].append(float(data[i]['data']['co']))
            so2[1].append(float(data[i]['data']['so2']))
    plt.subplot(4,2,1)
    plt.plot(timestamp[0], pm2_5[0], color='k')
    plt.title('ST102 PM2.5')
    plt.subplot(4,2,2)
    plt.plot(timestamp[0], pm10[0], color='k')
    plt.title('ST105 PM10')
    plt.subplot(4,2,3)
    plt.plot(timestamp[0], co[0], color='k')
    plt.title('ST102 CO')
    plt.subplot(4,2,4)
    plt.plot(timestamp[0], so2[0], color='k')
    plt.title('ST102 SO2')
    plt.subplot(4,2,5)
    plt.plot(timestamp[1], pm2_5[1], color='k')
    plt.title('ST105 PM2.5')
    plt.subplot(4,2,6)
    plt.plot(timestamp[1], pm10[1], color='k')
    plt.title('ST105 PM10')
    plt.subplot(4,2,7)
    plt.plot(timestamp[1], co[1], color='k')
    plt.title('ST105 CO')
    plt.subplot(4,2,8)
    plt.plot(timestamp[1], so2[1], color='k')
    plt.title('ST105 SO2')
    plt.subplots_adjust(hspace=0.8)

ani = FuncAnimation(plt.gcf(), animate, interval=1000)
plt.show()
