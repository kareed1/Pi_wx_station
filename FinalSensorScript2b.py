import board             #bme280 sensor
import busio             #bme280 sensor
import adafruit_bme280   #bme280 sensor
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
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

#Pressure at sea level
bme280.sea_level_pressure = 1013.4

#dewpoint constants
#b = 17.62
#c = 243.12

#-------------DS18B20 Sensor----------------#
class DS18B20(object):
    def __init__(self):        
        self.device_file = glob.glob("/sys/bus/w1/devices/28*")[0] + "/w1_slave"
        
    def read_temp_raw(self):
        f = open(self.device_file, "r")
        lines = f.readlines()
        f.close()
        return lines
        
    def crc_check(self, lines):
        return lines[0].strip()[-3:] == "YES"
        
    def read_temp(self):
        temp_c = -255
        attempts = 0
        
        lines = self.read_temp_raw()
        success = self.crc_check(lines)
        
        while not success and attempts < 3:
            time.sleep(.2)
            lines = self.read_temp_raw()            
            success = self.crc_check(lines)
            attempts += 1
        
        if success:
            temp_line = lines[1]
            equal_pos = temp_line.find("t=")            
            if equal_pos != -1:
                temp_string = temp_line[equal_pos+2:]
                temp_c = float(temp_string)/1000.0
        
        return temp_c

#--------------rainfall---------------------#
tip_sensor = gpiozero.Button(6) #using gpio 6 - pin 31
bucket_vol = 0.2794     #in mm

#---------------Wind speed------------------#
wind_speed_sensor = gpiozero.Button(5) #using gpio 5 - pin 29
radius = 0.09 #distance from center of anenometer to edge of a cup - in meters
time_interval = 10 #amount of time anemometer rotations are measured
circumference = (2*math.pi)*radius #circumference of anenometer circle

#-----------Wind direction-----------------#
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

#################################
########Take Measurements########
#################################

#Use of % is from string formatting - puts variable in its place
#0.2f - signifies 2 decimal places for a floating point number

#Rain is monitored first for 15 min, then time recorded, then other measurements are taken.
#Therefore, rainfall is the cumulative rain for the 15 min prior to time stamp...
#and wind, press, temp, RH are approximately at the time of the time stamp.

#rain measurement
tip_count = 0                #reset number of bucket tips
rain_time = time.time() + 900 #time to measure rain bucket tips; 15'
def tip():
    global tip_count
    tip_count = tip_count + 1
    #print(tip_count * bucket_vol)
while time.time() <= rain_time: #runs code for 15 min
    tip_sensor.when_pressed = tip
rainfall = round(tip_count * bucket_vol,2)

#Date/time stamps
Date = time.strftime("%d %b %Y")
Time = time.strftime("%H:%M")

#BME280 sensor readings
Temperature = ("%0.2f" % bme280.temperature)    #temperature
Corrected_Press = bme280.pressure + 36.1        #Correct for elevation
Pressure = ("%0.2f" % Corrected_Press)          #pressure
Rel_Humid = ("%0.2f" % bme280.humidity)         #relative humidity
    #gamma = (b * bme280.temperature /(c + bme280.temperature)) +
        #math.log(bme280.humidity / 100.0)
    #dewpoint = (c * gamma) / (b - gamma)
    
    #Soil Temperature
    #if __name__ == "__main__":
    #    obj = DS18B20()
    #    Soil_Temp = ("%0.2f" % obj.read_temp())
Soil_Temp = "NA"

#Date/time stamps
Date = time.strftime("%d %b %Y")
Time = time.strftime("%H:%M")

#wind speed
wind_count = 0      #reset counter for rotations
wind_time = time.time() + time_interval #set time to count anemometer revs; 10 s
def spin():
    global wind_count               #define a function
    wind_count = wind_count + 1     # adds a rotation each time switch in anemometer is closed
    #print("spin" + str(wind_count)) #prints number of anemometer rotations
while time.time() <= wind_time: #runs code for 10 sec.
    wind_speed_sensor.when_pressed = spin
rotations = wind_count/2 #pulse is measured 2x per full rotation of anemometer
distance_m = circumference * rotations  #distance outer tip of cup turns in time frame
wind_speed = round((distance_m/time_interval) * 1.18,2) #1.18 = "anenometor factor" takes into acct energy to spin
    
#wind direction
wind_voltage = round(adc.value*3.3,1)   #3.3 is for voltage from raspberry pi to sensor; round to one decimal
if not wind_voltage in volts:
    wind_direction = "NA"           #if erroneous voltage is given, NA is provided as direction
else:
    wind_direction = (volts[wind_voltage])  #wind direction in degrees from dictionary (above)


#############################
#####WRITE DATA TO .CSV######
#############################

#Write initial csv if needed
find_csv_files = glob.glob("/media/pi/D892-EF0A/WeatherData*.csv")  #find all WeatherData csv files
num_csv_files = len(find_csv_files)     #counts the number of WeatherData csv files in directory
full_file_name = "/media/pi/D892-EF0A/WeatherData1.csv"
if num_csv_files == 0:                  #If no .csv file present, create csv file w/ header
    full_file_name = "/media/pi/D892-EF0A/WeatherData1.csv"
    with open(full_file_name,'w',newline='') as f:  #create new csv file
        thewriter = csv.writer(f)
        thewriter.writerow(["Date","Time","Air_Temperature(C)", "Pressure(hPa)", "Rel_Humid(%)",
                        "Soil_Temperature(C)","Wind_Speed(m/s)","Wind_Direction(deg)","Rainfall (mm)"])
else:                               #If .csv is present, don't create a new one
    pass

#Write new csv in sequence if prior week is filled: outputs every 15 min = 672 outputs/week
find_csv_files2 = glob.glob("/media/pi/D892-EF0A/WeatherData*.csv")  #find all WeatherData csv files
input_file = open(find_csv_files2[-1],"r+")  #select last csv in list
reader_file = csv.reader(input_file)        #opens csv file
csv_num_lines = len(list(reader_file))      #count # of lines in selected csv file
#create additional csv file when last one is full (i.e. 1 week)
if csv_num_lines == 673:                    #1 line = header; 672 = 1 wk of measures @ 15 min increments
    file_name = "/media/pi/D892-EF0A/WeatherData"   #prefix of file name/directory
    num_in_sequence = num_csv_files + 1     #add 1 to the num of WeatherData files present in directory
    file_suffix = ".csv"                    #file extension
    full_file_name = file_name+str(num_in_sequence)+file_suffix #combine to create new file name
    with open(full_file_name,'w',newline='') as f:  #create new csv file
        thewriter = csv.writer(f)
        thewriter.writerow(["Date","Time","Air_Temperature(C)", "Pressure(hPa)", "Rel_Humid(%)",
                        "Soil_Temperature(C)","Wind_Speed(m/s)","Wind_Direction(deg)","Rainfall (mm)"])
else:
    pass                                #disregard and write to current csv

#Save new row of data to csv file
find_csv_files3 = glob.glob("/media/pi/D892-EF0A/WeatherData*.csv") #list all WeatherData csv files in directory
csv_2_save_2 = find_csv_files3[-1]              #select last csv file in directory
with open(csv_2_save_2,'a') as f:               #write data to csv
    thewriter = csv.writer(f)
    thewriter.writerow([Date,Time,Temperature,Pressure,Rel_Humid,Soil_Temp,
                        wind_speed,wind_direction,rainfall])
print(Date,Time,Temperature,Pressure,Rel_Humid,Soil_Temp,wind_speed,
      wind_direction,rainfall)
