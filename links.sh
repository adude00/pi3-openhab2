cd /opt/docker/openhab5/openhab_conf
rm -f Events.log Openhab.log
ln /opt/docker/openhab5/openhab_userdata/logs/events.log Events.log
ln /opt/docker/openhab5/openhab_userdata/logs/openhab.log Openhab.log
