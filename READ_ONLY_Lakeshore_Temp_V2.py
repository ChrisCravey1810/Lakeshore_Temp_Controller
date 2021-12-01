# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 16:23:31 2021
Author: Christopher Cravey
Lab: Dominique Laroche @ UF

"""

from matplotlib import ticker
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from lakeshore import Model372
import csv
import os
import sys
import datetime as dt
import time


#    Locate and initialize Lakeshore Model, must include USB Baude Rate (Typically 9600)
'''
####    NOTE: Always set Lakeshore to ETHERNET MODE by selecting 
####          "interface" --> "Enabled" --> "Ethernet"
####          after, copy ip_adress from "View IP_Config <Submenu>"
####          into my_instrument below.
'''
my_instrument = Model372(9600, ip_address = '169.254.110.0')

try:
    while True == True:
        start_time = dt.datetime.now()
        #ENTER CUSTOM FILENAME
        #OR 
        #LEAVE EMPTY ('') and a name will be generated based on today's date
        filename = ''
        
        
        
        
        # SET PARAMETERS
        channels       =      [6]                       # (MUST BE AN ARRAY) Which lakeshore channels to read 
        innerloop_wait =      60                        # (MUST BE AN INT) Wait time (seconds) between individual data points
        loop_runtime   =      1440                      # Length (Minutes) of run
        
         
        
        #Error catching when defining variables
        assert(isinstance(loop_runtime, int)), "'loop_runtime' variabel must be an int"
        assert(isinstance(channels, list)), "'channels' variable must be a list"  
        assert(isinstance(innerloop_wait, int)), "'innerloop_wait' variable must be an int"
        
        
        
        #Search Lakeshore Data for the same filename and increment if it already exists
        def run_number(filename):
            run = 1
            while os.path.exists(filename % run):
                run += 1
            return filename % run
        
        #If left empty the file will automatically be named "LakeshoreTemp" + (Today's Date)_ run number
        if len(filename) == 0:
            filename = str('Lakeshore Data/ReadOnly_LakeshoreTemp(' + start_time.strftime('%m') + '-' +\
                           start_time.strftime('%d') + '-' + start_time.strftime('%y') + ')_%s.csv')
            filename = run_number(filename)     #add index number to filename
            
        else:
            filename = str('Lakeshore Data/' + filename + ('_%s.csv'))
            
            filename = run_number(filename)     #add index number to filename
        
    
    
    
    
        
        #CREATE CSV TO SAVE DATA:
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            csv_header=['Time:']
            
            for n in range(len(channels)):
                csv_header.append(str('CH. ' + str(str(channels[n]) + ' (K):')))
                
            writer.writerow(csv_header)
            
                
        
        # Initialize arrays to store data
            x = []
            y = []
            
        #y is a 2-D array where each column cooresponds to temperature of channel being measured
            for l in range(len(channels)):
                y.append([])
                
        
        
        #Initialize figure, 1 subplot per each channel being measured
            fig, axs = plt.subplots(len(channels), 1, sharex = True, figsize=(10,6))
            plt.style.use('bmh')
         
        
        
        #animation funtion, each time it is called it takes data + updates figure
            def animate(i):
                # x is local time, accurate to seconds
                x.append(dt.datetime.now().strftime('%H:%M:%S')) 
                
                csv_input = []
                csv_input.append(x[i])        
        
                for k in range(len(channels)):
                    y[k].append(my_instrument.get_kelvin_reading(channels[k]))
                    
                    csv_input.append(y[k][i])
                    
                    if len(channels) > 1:
                        axs[k].clear()                #Plot data, make graph look nice
                        axs[k].plot(x, y[k])
                        axs[k].ticklabel_format(style = 'plain', useOffset = False, axis = 'y')
                        axs[k].set_ylabel(str('CH. ' + str(channels[k]) + ' Temp. (K)'))
                    
                    else:
                        axs.clear()                #Plot data, make graph look nice
                        axs.plot(x, y[k])
                        axs.ticklabel_format(style = 'plain', useOffset = False, axis = 'y')
                        axs.set_ylabel(str('CH. ' + str(channels[k]) + ' Temp. (K)'))
                
                #Write data
                writer.writerow(csv_input)
                file.flush()
                
                if len(channels) > 1:
                #Makes graph look nice and neat
                    axs[0].set_title('(READ ONLY) Temp vs Time', color = 'red')
                    axs[len(channels) - 1].set_xlabel('Local Time')
                    axs[len(channels) - 1].tick_params(axis = 'x', labelrotation = 50)
                    xticks = ticker.MaxNLocator(20)
                    axs[len(channels) - 1].xaxis.set_major_locator(xticks)
                    plt.subplots_adjust(bottom = 0.15, top = 0.92)
                
                else:
                    axs.set_title('(READ ONLY) Temp vs Time', color = 'red')
                    axs.set_xlabel('Local Time')
                    axs.tick_params(axis = 'x', labelrotation = 50)
                    xticks = ticker.MaxNLocator(20)
                    axs.xaxis.set_major_locator(xticks)
                    plt.subplots_adjust(bottom = 0.15, top = 0.92)
                    
        
        
        
        
            #This function calls the animate function after every interval, as set by the user
            #Interval = time between data points in milliseconds
            time.sleep(10)
            temp_data = FuncAnimation(fig, animate, interval = (innerloop_wait * 1000))
        
        
            #plt.pause() pauses execution of program while temp_data continues taking data
            print("Begin Measurements\nTaking data once every " + str(innerloop_wait) + " seconds.")
            plt.pause(loop_runtime * 60)
            
        
        
        #SAVE FIGURE
        fig.savefig(str(filename[:-4] + '.png'))    #replace .csv with .png
        plt.close()
        
        
        
        print("\n\nPlot has been saved, beginning new read only plot.")

except KeyboardInterrupt:
    print("Program halted")
    sys.exit(0)
