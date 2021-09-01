import board
from adafruit_bme280 import basic as adafruit_bme280
#import board             #bme280 sensor
#import busio             #bme280 sensor
#import adafruit_bme280   #bme280 sensor
import time
import datetime
import os, glob          #ds18b20 sensor
import csv
import gpiozero
import math
from gpiozero import MCP3008  

###############################
########Set up sensors#########
###############################

#----------------BME280 Sensor----------------#
# Create library object using our Bus I2C port
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

#--------------rainfall---------------------#
tip_sensor = gpiozero.Button(6) #using gpio 6 - pin 31
bucket_vol = 0.011     #bucket volume - inches
rain_time = 893  #time (in seconds) to measure rain bucket tips; 15'

#---------------Wind speed------------------#
wind_int = 5 #amount of time (in seconds) anemometer rotations are measured
wind_factor = 1.492 #wind speed of 1.492 mph causes switch to close 1x/sec
anem_factor = 1.18 #anemometer factor to acct for wind energy lost

#################################
########Take Measurements########
#################################

#rain measurement
tip_count = 0                #reset number of bucket tips
rain_time = time.time() + rain_time #time (in seconds) to measure rain bucket tips; 15'
def tip():
    global tip_count
    tip_count = tip_count + 1
while time.time() <= rain_time: #runs code for 15 min
    tip_sensor.when_pressed = tip
rainfall = round(tip_count * bucket_vol,2)

#BME280 sensor readings
Temperature = ("%0.2f" % (bme280.temperature * 9/5 + 32))          #convert C to F
Pressure = ("%0.2f" % bme280.pressure)          #pressure
Rel_Humid = ("%0.2f" % bme280.humidity)         #relative humidity
    
#wind speed
wind_speed_sensor = gpiozero.Button(5) #using gpio 5 - pin 29
wind_count = 0      #reset counter for rotations
wind_time = time.time() + wind_int #set time to count anemometer revs; 10 s
def spin():
    global wind_count               #define a function
    wind_count = wind_count + 1     # adds a rotation each time switch in anemometer is closed
    #print("spin" + str(wind_count)) #prints number of anemometer rotations
while time.time() <= wind_time: #runs code for 10 sec.
    wind_speed_sensor.when_pressed = spin
wind_speed = ("%0.2f" % ((wind_count * wind_factor) / wind_int * anem_factor))  #wind speed calculation

#wind direction
adc = MCP3008(channel=0)
#Dictionary to convert voltage reading to wind angle (voltage:angle)
volts = {
    0.4: 0.0,
    1.4: 22.5,
    1.2: 45.0,
    2.8: 67.5,
    2.7: 90.0,
    2.9: 112.5,
    2.2: 135.0,
    2.5: 157.5,
    1.8: 180.0,
    2.0: 202.5,
    0.7: 225.0,
    0.8: 247.5,
    0.1: 270.0,
    0.3: 292.5,
    0.2: 315.0,
    0.6: 337.5,
    }
wind_voltage = round(adc.value*3.3,1)   #3.3 is for voltage from raspberry pi to sensor; round to one decimal
if not wind_voltage in volts:
    wind_direction = "NA"           #if erroneous voltage is given, NA is provided as direction
else:
    wind_direction = (volts[wind_voltage])  #wind direction in degrees from dictionary (above)

#Date/time stamps
Date = time.strftime("%d %b %Y")
Time = time.strftime("%H:%M")

#############################
#####WRITE DATA TO .CSV######
#############################

#Write initial csv if needed
find_csv_files = glob.glob("/media/pi/D892-EF0A/data_files/WeatherData*.csv")  #find all WeatherData csv files
num_csv_files = len(find_csv_files)     #counts the number of WeatherData csv files in directory
if num_csv_files == 0:                  #If no .csv file present, create csv file w/ header
    full_file_name = "/media/pi/D892-EF0A/data_files/WeatherData1.csv"
    with open(full_file_name,'w',newline='') as f:  #create new csv file
        thewriter = csv.writer(f)
        thewriter.writerow(["Date","Time","Air_Temperature(F)", "Pressure(hPa)", "Rel_Humid(%)",
                        "Wind_Speed(mph)","Wind_Direction(deg)","Rainfall(in)"])
else:                               #If .csv is present, don't create a new one
    pass

#Write new csv in sequence if prior week is filled: outputs every 15 min = 672 outputs/week
find_csv_files2 = glob.glob("/media/pi/D892-EF0A/data_files/WeatherData*.csv")  #find all WeatherData csv files
input_file = open(find_csv_files2[-1],"r+")  #select last csv in list
reader_file = csv.reader(input_file)        #opens csv file
csv_num_lines = len(list(reader_file))      #count # of lines in selected csv file
#create additional csv file when last one is full (i.e. 1 week)
if csv_num_lines >= 673:                    #1 line = header; 672 = 1 wk of measures @ 15 min increments
    file_name = "/media/pi/D892-EF0A/data_files/WeatherData"   #prefix of file name/directory
    num_in_sequence = num_csv_files + 1     #add 1 to the num of WeatherData files present in directory
    file_suffix = ".csv"                    #file extension
    full_file_name = file_name+str(num_in_sequence)+file_suffix #combine to create new file name
    with open(full_file_name,'w',newline='') as f:  #create new csv file
        thewriter = csv.writer(f)
        thewriter.writerow(["Date","Time","Air_Temperature(F)", "Pressure(hPa)", "Rel_Humid(%)",
                        "Wind_Speed(mph)","Wind_Direction(deg)","Rainfall(in)"])
else:
    pass                                #disregard and write to current csv

#Save new row of data to csv file
find_csv_files3 = glob.glob("/media/pi/D892-EF0A/data_files/WeatherData*.csv") #list all WeatherData csv files in directory
csv_2_save_2 = find_csv_files3[-1]              #select last csv file in directory
with open(csv_2_save_2,'a') as f:               #write data to csv
    thewriter = csv.writer(f)
    thewriter.writerow([Date,Time,Temperature,Pressure,Rel_Humid,
                        wind_speed,wind_direction,rainfall])
print(Date,Time,Temperature,Pressure,Rel_Humid,wind_speed,
      wind_direction,rainfall)
