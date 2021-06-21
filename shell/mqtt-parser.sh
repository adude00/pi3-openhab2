#!/bin/bash
#
# workaround per evitare questo delirio https://community.openhab.org/t/solved-double-quotes-etc-in-executecommandline/88426


COMMAND=/tmp/ac-cmd

echo /usr/bin/mosquitto_pub -h localhost -t '"cmnd/ir01/irhvac"' -m '"{ Vendor: COOLIX, Power: '$1', Mode:'$2', Temp:'$3', FanSpeed:'$4' }"' > $COMMAND

chmod a+x $COMMAND
cat $COMMAND

exec $COMMAND
