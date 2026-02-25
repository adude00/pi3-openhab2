# Persistance 2026

Sono rimaste solo due persistance:

* mapdb
* influxdb

## MapDB

MapDB si salva solo ed esclusivamente l'ultimo stato di un item, e nient'altro: non si salva gli stati precedenti, non si salva QUANDO è stato aggiornato, etc.

Però è fondamentale che TUTTI GLI ITEMS scrivano su mapdb il loro stato ad ogni aggiornamento affinchè MapDB possa ripristinare lo stato precendente al boot.

Senza MapDB al boot ogni singolo ITEM è NULL: immagina avere OpenHAB con tutte le tue belle configurazioni settate negli anni tutte a NULL!!!

## InfluxDB

InfluxDB lo conosciamo, c'è poco da dire. Nonostante quanto scritto sopra, per avere stati come `.lastUpdate` e la `media degli ultimi X minuti` degli items, **influxdb è la persistance di default**.

Questa cosa si configura da interfaccia, non da shell.

## Altre persistance

Con l'aggiornamento alla 5 **non sono necessarie altre persistance**.

Non ce ne sono di installate: si installano [e configurano](https://i.vgy.me/sQA0IQ.png) da interfaccia.

```bash
root@pi5:~/openhab_conf/persistence# ll |grep -v disable
total 32
-rw-r--r-- 1 openhab openhab 1870 Oct 30 11:02 README.md
-rw-r--r-- 1 openhab openhab  359 Dec 12 10:52 influxdb.persist
-rw-r--r-- 1 openhab openhab  429 Feb 23 11:18 mapdb.persist
-rw-r--r-- 1 openhab openhab  256 Oct 30 11:02 readme.txt
root@pi5:~/openhab_conf/persistence# 
```


# DOCUMENTAZIONE VECCHIE OBSOLETE

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
