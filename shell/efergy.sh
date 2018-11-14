#!/bin/bash

KWH=`curl -s http://www.energyhive.com/mobile_proxy/getCurrentValuesSummary?token=D2ZDntk8uszYL957qPHc5mzvgsWFTrhM | jq '.[].data[0]' |grep ":" |awk '{ print $2 }'`

MIN="200"

if [ "$KWH" -lt "$MIN" ]
  then
    echo 0
  else
    echo $KWH
  fi
