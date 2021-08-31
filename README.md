# Pi_wx_station
Raspberry Pi weather station script

File is ran using: sudo python3 filename.py.

Script is only set to run 1x, then it writes output to csv file.

To run it more than once, I set it as a cron job (see cron job script).

Parts of code borrowed from https://projects.raspberrypi.org/en/projects/build-your-own-weather-station

Sensors: BME280 (temp, humidity, pressure), DS18b20 (soil temp), SwitchDoc Labs WeatherRack (wind direction/speed and rainfall)
