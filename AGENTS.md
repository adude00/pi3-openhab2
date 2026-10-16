# Workspace Description

This is an OpenHAB 5 configuration directory, installed [via official docker images](https://hub.docker.com/r/openhab/openhab).

root@pi5:/opt/docker/openhab5# tree -L1
.
├── Events.log -> openhab_userdata/logs/events.log    # hardlinked here
├── Openhab.log -> openhab_userdata/logs/openhab.log  # hardlinked yere
├── docker-compose.yml -> openhab_conf/docker-compose.yml
├── openhab_addons
├── openhab_conf # <--  YOU ARE HERE
└── openhab_userdata


# Peculiarities of working here

Any file with a proper extension (.rules, .items, .things, etc) gets loaded immediately in production: while working on a file use a different extension to avoid loading it multiple times and filling the logs with errors. 

Rename it properly only when done.


# Checking your work

After your edits, check Openhab.log for errors in loading the configuration item. 

Note that it takes a while to process new and edited files: wait some (30?) seconds before declaring victory.


# Items status information

Events.log will have current and past status of items.


# Alexa Integration

In order to have a switch controlled by alexa just add `{alexa="Switch"}` to the item configuration


# Repository rules

Do NOT commit unless told so.
