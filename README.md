# Repo info

Questo repo è la dir openhab_conf di un installazione con docker di OpenHAB 5 (https://hub.docker.com/r/openhab/openhab/).

/opt/docker/openhab5# tree -L 1
├── Events.log -> openhab_userdata/logs/events.log
├── Openhab.log -> openhab_userdata/logs/openhab.log
├── README.md -> openhab_conf/README.md <- QUESTO FILE
├── docker-compose.yml -> openhab_conf/docker-compose.yml <- in questa dir e linkato in ../
├── logs -> openhab_userdata/logs/
├── openhab-init.d
├── openhab-ssh
├── openhab_addons
├── openhab_conf
└── openhab_userdata

Questo repo contiene i files di configurazione di OpenHAB, più il README.md ed il docker-compose.yml

E' sia un configuration-management che una sorta di backup.

Attualmente abbiamo installato la release 5, versione 5.1.4.

# Install info

## docker-compose.yml

L'immagine è hardcodata perchè gli aggiornamenti li voglio verificare prima.

Per ora si usa la default debian

```
    image: "openhab/openhab:5.0.3"
```

## Directory Mappings: 

Standard Directory Mappings:

* /var/lib/openhab2 > `openhab_userdata`
* /etc/openhab2 > `openhab_conf`

Sauce: https://community.openhab.org/t/openhab-cli-in-a-docker-container/137222/4

## Customizzazioni

Le customizzazioni presenti sono:

* client openssh
* pacchetto wakeonlan
* pacchetto jq

Per realizzarle, nel file `docker-compose.yml` ci sono due volumi aggiuntivi:
```yml
      - "./openhab-init.d:/etc/cont-init.d"
      - "./openhab-ssh:/openhab/.ssh"
```

### Dir ./openhab-init.d
Tutti i contenuti di `./openhab-init.d` vengono eseguiti al boot del container

Attualmente c'è un solo file, `50-software`.

### File ./openhab-init.d/50-software

Il conteuto è il seguente 
```bash
#!/bin/bash

if ssh -V &>/dev/null
then
  echo OLD IMAGE - Software is installed
else
  echo NEW IMAGE - Need to install openssh-client wakeonlan jq
  apt update || true
  apt -y install openssh-client wakeonlan jq || true
fi
```

### Dir ./openhab-ssh
Questa è la dir `.ssh` dell'utente con cui gira openhab dentro il container.

I files sono:
```
 1823 Oct 30 11:02 id_rsa
  393 Oct 30 11:02 id_rsa.pub
 2220 Oct 30 11:02 known_hosts
```



# DEBUG

## Start in debug

docker run -it openhab/openhab:VERSION ./start_debug.sh

## openhab-cli
docker exec -it openhab5 /openhab/runtime/bin/client

## Shell
docker exec -it openhab5 /bin/bash


# Upgrades

## 5.0.3 > 5.1.3

Fatta il 20260223, è stato necessario:

* Togliere la default strategy da tutti i file di conf delle persistance [perchè deprecata](https://www.openhab.org/blog/2025-12-22-openhab-5-1-release.html#default-persistence-deprecated)
* Un riavvio per riparare alcuni mqtt (tapparelle P1 e clima Camera 2 IR)
* Spegnere e riaccendere il termostato del soggiorno ha sistemato il timer a 5 min anzichè 10


# Appunti alpine

## Alpine SSH

In caso di migrazione ad Alpine, considerare questo comando per installare ssh

`apk add --update --no-cache openssh`

Va ancora capito:
* come eseguire comandi al boot del container
* come è mappata la dir .ssh
* se i pacchetti utilizzano gli stessi path
* se alla fine poi funziona veramente tutto

# History migrazione v2

## 20250710-1426: rimosso mqtt v1
2025-07-10 14:23:41.323 [thome.event.ExtensionEvent] - Extension 'binding-mqtt1' has been uninstalled.

## 20250710-1508: rimosso exec v1
2025-07-10 15:08:33.312 [thome.event.ExtensionEvent] - Extension 'binding-exec1' has been uninstalled.
