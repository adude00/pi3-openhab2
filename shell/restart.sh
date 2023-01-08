#!/bin/bash

date >> /var/log/openhab-restart
service openhab2 restart >> /var/log/openhab-restart
echo >> /var/log/openhab-restart
