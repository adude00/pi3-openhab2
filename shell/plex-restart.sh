ssh root@opti midclt call chart.release.scale plex \'{\"replica_count\": 0}\'
sleep 10
ssh root@opti midclt call chart.release.scale plex \'{\"replica_count\": 1}\'
