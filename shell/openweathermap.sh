#!/bin/bash
APIKEY=c6fa10fbdc077288779d79c727e4ba54
LAT=44.48
LON=11.37
WRKDIR=/tmp/openweathermap
WRKFILE=$WRKDIR/rawdata

mkdir -p $WRKDIR
curl -s "http://api.openweathermap.org/data/2.5/weather?lat=$LAT&lon=$LON&units=metric&APPID=$APIKEY" > $WRKFILE

# TEMP
cd $WRKDIR
cat $WRKFILE |jq .main.temp > main-temp
cat $WRKFILE |jq .main.humidity > main-humidity
cat $WRKFILE |jq .wind.speed > wind-speed
#cat $WRKFILE |jq .weather.description > weather-description

