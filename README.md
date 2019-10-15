# Install howto - 2019 10 15

## Preparing the system 
In order to install openhab2 on raspberry *after crash* do the following:

```
apt update
apt upgrade
apt install vim openjdk-8-jdk jq telnet bc lrzsz mosquitto mc git htop
```

## Installing openhab from repositories
Let's now install `openhab2`
```
wget -qO - 'https://bintray.com/user/downloadSubjectPublicKey?username=openhab' | sudo apt-key add -
sudo apt-get install apt-transport-https
echo 'deb https://dl.bintray.com/openhab/apt-repo2 stable main' | sudo tee /etc/apt/sources.list.d/openhab2.list
sudo apt-get update && sudo apt-get install openhab2 openhab2-addons openhab2-addons-legacy
```

## Restoring conf
You can now restore your conf from backup. You got to restore the following dirs:

- `/etc/openhab2`
- `/var/lib/openhab2`

## Starting openhab
You should now be able to start openhab2. FIRST BOOT WILL BE *SLOW* (5 mintues)!!!

## If things still do not work
You can manually check that the following folders are restored:

```
* /etc/openhab2                                  # Conf dir. It's on github. That's easy.
* /var/lib/openhab2/.ssh/                        # So it will be able to turn on and off the NAS
* /var/lib/openhab2/config/org/openhab/          # During the next boot it will install what's needed and remove what's not
* /var/lib/openhab2/persistence/                 # Graphs will work now
* /var/lib/openhab2/jsondb/homekit.json          # Homekit configuration, then you won't have to add it back to iOS devices
* /var/lib/openhab2/influxdb.cfg                 # InfluxDB conf. It's linked from /etc/openhab2 because it contains passwords
```

### Old guide
The old guide is in RECOVERY.md file. All its information should be here but you can check it out.

# Installing mosquitto
It's super easy:
```
apt install mosquitto
```

Then restore `/etc/mosquitto` from backups.

# Cron and scripts
First restore the crontab of the users (they're in the backup):
* `root`
* `openhab` 

Then add */mnt/temp* to */etc/fstab*
```
# temperature
pi:/opt/temp	/mnt/temp	nfs	_netdev	0	0
```

Then restore:
* `/opt/script/`
* `/opt/backup/`
