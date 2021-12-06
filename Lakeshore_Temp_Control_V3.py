'''
Created on September 5th, 2021
Author: Christopher Cravey
Lab: Dominique Laroche @ UF
'''
from matplotlib import ticker
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from lakeshore import Model372
from lakeshore.model_372 import Model372HeaterOutputSettings, \
Model372OutputMode, Model372Polarity
import csv
import os
import datetime as dt
import time
start_time = dt.datetime.now()

#    Locate and initialize Lakeshore Model, must include USB Baude Rate (Typically 9600)
'''
####    NOTE: Always set Lakeshore to ETHERNET MODE by selecting 
####          "interface" --> "Enabled" --> "Ethernet"
####          after, copy ip_adress from "View IP_Config <Submenu>"
####          into my_instrument below.
'''
my_instrument = Model372(9600, ip_address = '169.254.25.66')


#ENTER CUSTOM FILENAME
#OR 
#LEAVE EMPTY ('') and a name will be generated based on today's date
filename = ''

'''
#Initialize Heater with Closed_Loop setting (Without this step, heater will not turn on)
Closed_Loop_Settings = Model372HeaterOutputSettings( output_mode = Model372OutputMode.CLOSED_LOOP, 
                                            input_channel = 6, powerup_enable = True, 
                                            reading_filter = False, delay = 1, 
                                            polarity = Model372Polarity.UNIPOLAR)
my_instrument.configure_heater(0, Closed_Loop_Settings)
'''





#CHOOSE HEATER TYPE
#Choose if you want to control heater via PID or manual heater percentages

CLOSED_LOOP_PID    =      True                #Utilizes PID settings and a given setpoint/ramp rate
OPEN_LOOP          =      False               #Simply turns on heater to a constant user set power percentage, no setpoint



#SET PARAMETERS

channels           =      [6]                 # (MUST BE AN ARRAY) Which lakeshore channels to read 
innerloop_wait     =      3                   # (MUST BE AN INT) Wait time (seconds) between individual data points


setpoint           =      [0.010]             # Must be in Kelvin,         only used during CLOSED LOOP 
setpoint_ramprate  =      [10]                # Kevlin/Min Ramp Rate,      only used during CLOSED LOOP           
loop_runtime       =      [30]               # Length (Minutes) of each loop
newloop_wait       =      [5]                 # Wait time (seconds) before taking data from a new loop


heater_range       =      [0]       #See dictionary below for values
'''                                Dictionary of heater_range values...
#                                       OFF       :    0
#                                       31.6uA    :    1
#                                       100uA     :    2 
#                                       316uA     :    3
#                                       1mA       :    4   
#                                       3.16mA    :    5
#                                       10mA      :    6
#                                       31.6mA    :    7
#                                       100mA     :    8
'''

P                  =      [60]           ; '''PID is for CLOSED LOOP PID'''         
I                  =      [30]           #(MUST BE AN ARRAY) same length as loop_runtime
D                  =      [6]            


manual_output      =      [15]           ; '''manual_output is for OPEN LOOP'''          
                                         #(MUST BE AN ARRAY) should be percentage (0 - 100) of heater power desired


 

#Error catching when defining variables
assert(isinstance(CLOSED_LOOP_PID, bool)),      "CLOSED_LOOP_PID must be True/False"
assert(isinstance(OPEN_LOOP, bool)),            "OPEN_LOOP must be True/False"
assert(CLOSED_LOOP_PID != OPEN_LOOP),           "Either OPEN_LOOP or CLOSED_LOOP must be True"
if CLOSED_LOOP_PID == True:
    assert(len(setpoint)==len(setpoint_ramprate)==len(loop_runtime)==len(newloop_wait)==len(P)==len(I)==len(D)==len(heater_range)), \
                                                "Make sure that (setpoint, loop_runtime, newloop_wait, P, I, D, and heater_range) all are LISTS with equal length"
else:
    assert(len(loop_runtime)==len(newloop_wait)==len(manual_output)==len(heater_range)), \
                                                "Make sure that (setpoint, loop_runtime, newloop_wait, manual_ouput, and heater_range) all are LISTS with equal length"
assert(isinstance(channels, list) & isinstance(channels[0], int)),             "'channels' variable must be a list containing integer(s)"  
assert(isinstance(innerloop_wait, int)),        "'innerloop_wait' variable must be an int"



#Initialize either a closed loop or open loop heater (Without this step, heater will not turn on)
if CLOSED_LOOP_PID == True:
    Closed_Loop_Settings = Model372HeaterOutputSettings( output_mode = Model372OutputMode.CLOSED_LOOP, 
                                                input_channel = 6, powerup_enable = True, 
                                                reading_filter = False, delay = 1, 
                                                polarity = Model372Polarity.UNIPOLAR)
    my_instrument.configure_heater(0, Closed_Loop_Settings)


if OPEN_LOOP == True:
    Open_Loop_Settings = Model372HeaterOutputSettings( output_mode = Model372OutputMode.OPEN_LOOP, 
                                                input_channel = 6, powerup_enable = True, 
                                                reading_filter = False, delay = 1, 
                                                polarity = Model372Polarity.UNIPOLAR)
    my_instrument.configure_heater(0, Open_Loop_Settings)





#Search Lakeshore Data for the same filename and increment if it already exists
def run_number(filename):
    run = 1
    while os.path.exists(filename % run):
        run += 1
    return filename % run


#If filename = '', the file will automatically be named "LakeshoreTemp" + (Today's Date)_ run number
if len(filename) == 0:
    filename = str('Lakeshore Data/LakeshoreTemp(' + start_time.strftime('%m') + '-' +\
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
            axs[0].set_title('Lakeshore Temperature VS Time')
            axs[len(channels) - 1].set_xlabel('Local Time')
            axs[len(channels) - 1].tick_params(axis = 'x', labelrotation = 50)
            xticks = ticker.MaxNLocator(20)
            axs[len(channels) - 1].xaxis.set_major_locator(xticks)
            plt.subplots_adjust(bottom = 0.15, top = 0.92)
        
        else:
            axs.set_title('Lakeshore Temperature VS Time')
            axs.set_xlabel('Local Time')
            axs.tick_params(axis = 'x', labelrotation = 50)
            xticks = ticker.MaxNLocator(20)
            axs.xaxis.set_major_locator(xticks)
            plt.subplots_adjust(bottom = 0.15, top = 0.92)
            




#This function calls the animate function after every interval, as set by the user
#Interval = time between data points in milliseconds
    temp_data = FuncAnimation(fig, animate, interval = (innerloop_wait * 1000))


#For loop of the actual time loops
    for j in range(len(loop_runtime)):
        print('Setting new param...\n')
        
        my_instrument.set_heater_output_range(0, heater_range[j])
        print("Heater Range set to: ", my_instrument.get_heater_output_range(0))
        
        
        if CLOSED_LOOP_PID == True:
            my_instrument.set_heater_pid(0, P[j], I[j], D[j])
            pid = my_instrument.get_heater_pid(0)
            print("Using CLOSED LOOP PID settings")
            print("PID set to: ", 'P: ', pid['gain'], 'I: ', pid['integral'], 'D: ', pid['ramp_rate'])
        
            my_instrument.set_setpoint_ramp_parameter(0, True, setpoint_ramprate[j])
            my_instrument.set_setpoint_kelvin(0, setpoint[j])
            print("Setpoint set to: ", setpoint[j], "K")
            print("Setpoingt being ramped at a rate of ", setpoint_ramprate[j], "K/min")
            
        if OPEN_LOOP == True:
            my_instrument.set_manual_output(0, manual_output[j])
            print("Using OPEN LOOP settings")
            print("Manual output set to: ", my_instrument.get_manual_output(0), " percent")
            
        
      
        
        print('Waiting before taking data...')
        time.sleep(newloop_wait[j])
    #plt.pause() pauses execution of program while temp_data continues taking data
        print('Begin loop ', j + 1)
        plt.pause(loop_runtime[j] * 60)
        
    #SAVE FIGURE
        fig.savefig(str(filename[:-4] + '.png'))    #replace .csv with .png
        print('end loop ', j + 1, '\n')


print('\n\n\nAll loops complete...')


#plt.close()


'''Optional: Turn Heater Off
heater_OFF = Model372HeaterOutputSettings( output_mode = Model372OutputMode.OFF, 
                                            input_channel = 6, powerup_enable = True, 
                                           reading_filter = False, delay = 1, 
                                            polarity = Model372Polarity.UNIPOLAR)
my_instrument.configure_heater(0, heater_OFF)
print("Heater has been turned off")
'''

print("End of Measurements!\nPlease make sure to leave the heater on the setting you desire.")


