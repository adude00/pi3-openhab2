# OPENHAB2 RECOVERY PROCEDURE

## Cleaning the system

Move (because you back them up already) the following dirs:
* /etc/openhab2
* /var/lib/openhab2
* /usr/share/openhab2

Then list installed packages and remove everything with purge

    # apt list --installed |grep openhab2

    WARNING: apt does not have a stable CLI interface yet. Use with caution in scripts.

    openhab2/stable,now 2.4.0-1 all [installed]
    openhab2-addons/stable,now 2.4.0-1 all [installed]
    openhab2-addons-legacy/stable,now 2.4.0-1 all [installed]

Then **apt-get remove --purge** every single package

    apt-get remove --purge openhab2 openhab2-addons openhab2-addons

## Installing from scratch

Install openhab from the repo:

    apt-get install screen mc vim git htop openhab2 openhab2 openhab2-addons openhab2-addons-legacy

## First start

You should start it the first time to see if its working. It should work as expected.

**Give it some time on the first boot**, it can take 5 minutes until you see the first log!!

After it turned on without problems, turn it off and start the restoring procedure.

## Restoring the conf

Restore /etc/openhab2 dir first, then turn it on, check that it load it correctly, then turn it off.

## The fun part

Now you got to restore a few other files.

* /var/lib/openhab2/.ssh/                        # So it will be able to turn on and off the NAS
* /var/lib/openhab2/config/org/openhab/          # During the next boot it will install what's needed and remove what's not
* /var/lib/openhab2/persistence/                 # Graphs will work now
* /var/lib/openhab2/jsondb/homekit.json          # Homekit configuration, then you won't have to add it back to iOS devices

## The big bet

Now you should start. It will first install what's needed, remove what's not needed, then everything should kinda be the way it was before.

If not, figure out what did you forget and come back to update this guide.
