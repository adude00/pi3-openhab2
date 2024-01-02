#!/bin/bash
MYDIR="$(dirname "$(which "$0")")"
source $MYDIR/bearer.sh

TMPFILE=/dev/shm/climaGiochiCurlOutput
RUNFILE=/dev/shm/climaGiochiRun

# POWER
POWER=$1
if [ "$1" == ON ]; then
  POWER=1
fi

if [ "$1" == OFF ]; then
  POWER=0
fi

if [ -z "$2" ]; then
    echo "Usage:" 1>&2
    echo "       $0 [ON/OFF] [Temp in C] [FAN (0: Auto, 5:Very Low, 9: Very High)]" 1>&2
    echo "Example:" 1>&2
    echo "       $0 ON 18 0" 1>&2
    exit 1
fi

# TEMPERATURE
TEMP=$2

# FAN SPEED
if [ -z "$3" ]; then
  FAN=0
else
  FAN=$3
fi


# DEBUG
echo $0 $POWER $TEMP $FAN >> /var/log/openhab2/set-climaGiochi.log
# For dry run uncomment below
#exit




sendcurl () {
rm -f $TMPFILE
curl --connect-timeout 2 -m 5 -s -X 'POST' \
  'https://api.connectlife.io/api/v1/appliance' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer '$BEARER \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "id": "8650051000200030003000000f7f60c2690d-8650051000200030003000000f7f60c2690d",
    "properties": {
      "Power": "'$POWER'",
      "SetTemperature": "'$TEMP'",
      "FanSpeed": "'$FAN'"
    }
  }
]'  > $TMPFILE

}


# Crappy API timeouts often - this mostly solves the issue

# Check if we're not already running
if test -f "$RUNFILE"; then
    echo "$RUNFILE exists. Already running. Exiting."
    exit 1
fi
touch $RUNFILE

# Try a few times until it works
counter=1
until [ $counter -gt 30 ]
do
  echo "Try $counter ..."
  sendcurl
  sleep 1
  if [ $(grep 8650051000200030003000000f7f60c2690d-8650051000200030003000000f7f60c2690d $TMPFILE |wc -l) == "1" ]; then
    counter=999
  else
    ((counter++))
  fi
done

# Removing the file
rm -f $RUNFILE
