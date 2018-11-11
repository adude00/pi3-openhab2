#!/bin/bash

 #Enter your ip of your device here
DEVICES="172.27.72.9"

for i in `echo $DEVICES`; do
    # Change dev and eth0 if needed
    ip neigh flush dev eth0 $i
    hping3 -2 -c 10 -p 5353 -i u1 $i -q >/dev/null 2>&1
    sleep 0.5
    # Only arp specific device, grep for a mac-address
    status=`arp -an $i | awk '{print $4}' | grep "..:..:..:..:..:.." |wc -l`
    statusMessage="OFF"
    #A mac will be 17 characters including the ":"
    if [ ${status} -eq 1 ]; then
        statusMessage="ON"
    fi
done
echo $statusMessage
