> Historical reference only. This is the previous persistence README;
> some statements do not match the current configuration.
> See [the current documentation](../persistence/README.md) for active settings.

# Persistence 2026

Only two persistence services remain:

* mapdb
* influxdb

## MapDB

MapDB stores only the latest state of an Item, and nothing else: it does not store previous states, WHEN the Item was updated, etc.

However, it is essential that ALL ITEMS write their state to MapDB on every update so that MapDB can restore their previous state at startup.

Without MapDB, every single ITEM is NULL at startup: imagine having all your carefully configured OpenHAB settings, built up over the years, reset to NULL!!!

## InfluxDB

We already know InfluxDB; there is little to add. Despite the above, to obtain values such as `.lastUpdate` and an Item's `average over the last X minutes`, **InfluxDB is the default persistence service**.

This is configured through the UI, not the shell.

## Other persistence services

After upgrading to version 5, **no other persistence services are needed**.

No others are installed: persistence services are installed [and configured](https://i.vgy.me/sQA0IQ.png) through the UI.

```bash
root@pi5:~/openhab_conf/persistence# ll |grep -v disable
total 32
-rw-r--r-- 1 openhab openhab 1870 Oct 30 11:02 README.md
-rw-r--r-- 1 openhab openhab  359 Dec 12 10:52 influxdb.persist
-rw-r--r-- 1 openhab openhab  429 Feb 23 11:18 mapdb.persist
-rw-r--r-- 1 openhab openhab  256 Oct 30 11:02 readme.txt
root@pi5:~/openhab_conf/persistence# 
```


# OLD, OBSOLETE DOCUMENTATION

OpenHAB manages persistance in a weird and convoluted way.

There are many persistances, this are the three kind we're using here:

## Different persistance engines

### RRJD4
The old and good rrd4j. Simple nerdy graphs with not a lot of informations. The data is stored in 
  /var/lib/openhab2/persistence/rrd4j

### mapdb
The thing that should be an included default, but is not: IT JUST REMEMBERS THE LAST FUCKING VALUE!!! It's for when you turn the thing off and on again and you don't want all the items in an **UNSET** state. It's just stupid that it's a plugin and not part of the project

### INFLUXDB
A time series database. Like any old database you need an ip, a port, a schema and some sort of auth. Then it can be queried.


## How we're using them

We have to set the system default to rrd4j otherwise graphs in sitemaps dont work. Don't ask me why. It's not written anywhere, it's just the way it is.

Then we have to make sure that everything is written to mapdb, because we don't want to turn on oepnhab and have unset things. 

This is mapdb.persist, the **real** default:

    Strategies {
        default = everyUpdate
    }

    Items {
        // DEFAULT EVERY ITEM: persist all items on every change (but do not restore on startup!!)
        * : strategy = everyChange, restoreOnStartup
    }

Then for both rrd4j and influxdb we work with groups. I made a group called gGraph which is what rrd4j saves, for influxdb I wasnt that smart but it's a work in progres. It's not a big problem if RRD4J saves everything but it's just stupid because you don't need the history of the state of a lamp for two years. Same for influxdb. 

## Conclusion

We're **de facto** defaulting to **mapdb**, but OpenHAB does not know as it has to think that the default engine is **rrd4j** even when it's just used for some graphs.

Yes, that's stupid.
