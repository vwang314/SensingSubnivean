import time
import csv
import sys, os
import matplotlib.pyplot as plt    
    
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
plt.show()