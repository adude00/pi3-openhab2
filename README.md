# English

## Repository information

This repository is the `openhab_conf` directory of a Docker installation of OpenHAB 5 (https://hub.docker.com/r/openhab/openhab/).

```text
/opt/docker/openhab5# tree -L 1
├── Events.log -> openhab_userdata/logs/events.log
├── Openhab.log -> openhab_userdata/logs/openhab.log
├── README.md -> openhab_conf/README.md <- THIS FILE
├── docker-compose.yml -> openhab_conf/docker-compose.yml <- in this directory and symlinked in ../
├── logs -> openhab_userdata/logs/
├── openhab-init.d
├── openhab-ssh
├── openhab_addons
├── openhab_conf
└── openhab_userdata
```

This repository contains the OpenHAB configuration files, along with `README.md` and `docker-compose.yml`.

It serves both as configuration management and as a form of backup.

To see which version we are running now, check `docker-compose.yml`.
 
The repository is named `openhab2` because version 2 was previously installed.

## Installation information

### docker-compose.yml

The image version is hardcoded because I want to check updates before applying them.

For now, the default Debian image is used.

```
    image: "openhab/openhab:5.1.4"
```

### Directory mappings

Standard directory mappings:

* /var/lib/openhab2 > `openhab_userdata`
* /etc/openhab2 > `openhab_conf`

Source: https://community.openhab.org/t/openhab-cli-in-a-docker-container/137222/4

### Customizations

The following customizations are included:

* OpenSSH client
* wakeonlan package
* jq package

To support them, `docker-compose.yml` includes two additional volumes:

```yml
      - "./openhab-init.d:/etc/cont-init.d"
      - "./openhab-ssh:/openhab/.ssh"
```

#### Directory ./openhab-init.d

All contents of `./openhab-init.d` are executed when the container starts.

Currently, there is only one file, `50-software`.

#### File ./openhab-init.d/50-software

Its contents are as follows:

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

#### Directory ./openhab-ssh

This is the `.ssh` directory of the user running openhab inside the container.

The files are:

```
 1823 Oct 30 11:02 id_rsa
  393 Oct 30 11:02 id_rsa.pub
 2220 Oct 30 11:02 known_hosts
```

## Debugging

### Start in debug mode

```bash
docker run -it openhab/openhab:VERSION ./start_debug.sh
```

### openhab-cli

```bash
docker exec -it openhab5 /openhab/runtime/bin/client
```

### Shell

```bash
docker exec -it openhab5 /bin/bash
```

## Upgrades

### 5.0.3 > 5.1.3

Performed on 20260223. The following steps were necessary:

* Remove the default strategy from all persistence configuration files [because it is deprecated](https://www.openhab.org/blog/2025-12-22-openhab-5-1-release.html#default-persistence-deprecated).
* Restart to fix some MQTT devices (P1 roller shutters and Camera 2 IR air conditioning).
* Power the living room thermostat off and on again to fix the timer, setting it to 5 minutes instead of 10.

## Alpine notes

### Alpine SSH

If migrating to Alpine, consider this command to install SSH:

`apk add --update --no-cache openssh`

The following still need to be figured out:

* How to run commands when the container starts.
* How the `.ssh` directory is mapped.
* Whether the packages use the same paths.
* Whether everything actually works in the end.

## Version 2 migration history

### 20250710-1426: removed mqtt v1

```text
2025-07-10 14:23:41.323 [thome.event.ExtensionEvent] - Extension 'binding-mqtt1' has been uninstalled.
```

### 20250710-1508: removed exec v1

```text
2025-07-10 15:08:33.312 [thome.event.ExtensionEvent] - Extension 'binding-exec1' has been uninstalled.
```

---

# Italiano

## Informazioni sul repository

Questo repository è la directory `openhab_conf` di un'installazione Docker di OpenHAB 5 (https://hub.docker.com/r/openhab/openhab/).

```text
/opt/docker/openhab5# tree -L 1
├── Events.log -> openhab_userdata/logs/events.log
├── Openhab.log -> openhab_userdata/logs/openhab.log
├── README.md -> openhab_conf/README.md <- QUESTO FILE
├── docker-compose.yml -> openhab_conf/docker-compose.yml <- in questa directory e collegato simbolicamente in ../
├── logs -> openhab_userdata/logs/
├── openhab-init.d
├── openhab-ssh
├── openhab_addons
├── openhab_conf
└── openhab_userdata
```

Questo repository contiene i file di configurazione di OpenHAB, insieme a `README.md` e `docker-compose.yml`.

Serve sia per la gestione della configurazione sia come forma di backup.

Per sapere quale versione è attualmente in esecuzione, consultare `docker-compose.yml`.

Il repository si chiama `openhab2` perché in precedenza era installata la versione 2.

## Informazioni sull'installazione

### docker-compose.yml

La versione dell'immagine è fissata esplicitamente perché voglio verificare gli aggiornamenti prima di applicarli.

Per ora si usa l'immagine Debian predefinita.

```
    image: "openhab/openhab:5.1.4"
```

### Mappatura delle directory

Mappature standard delle directory:

* /var/lib/openhab2 > `openhab_userdata`
* /etc/openhab2 > `openhab_conf`

Fonte: https://community.openhab.org/t/openhab-cli-in-a-docker-container/137222/4

### Personalizzazioni

Sono incluse le seguenti personalizzazioni:

* Client OpenSSH
* Pacchetto wakeonlan
* Pacchetto jq

Per supportarle, `docker-compose.yml` include due volumi aggiuntivi:

```yml
      - "./openhab-init.d:/etc/cont-init.d"
      - "./openhab-ssh:/openhab/.ssh"
```

#### Directory ./openhab-init.d

Tutti i contenuti di `./openhab-init.d` vengono eseguiti all'avvio del container.

Attualmente è presente un solo file, `50-software`.

#### File ./openhab-init.d/50-software

Il contenuto è il seguente:

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

#### Directory ./openhab-ssh

Questa è la directory `.ssh` dell'utente che esegue openhab all'interno del container.

I file sono:

```
 1823 Oct 30 11:02 id_rsa
  393 Oct 30 11:02 id_rsa.pub
 2220 Oct 30 11:02 known_hosts
```

## Debug

### Avvio in modalità debug

```bash
docker run -it openhab/openhab:VERSION ./start_debug.sh
```

### openhab-cli

```bash
docker exec -it openhab5 /openhab/runtime/bin/client
```

### Shell

```bash
docker exec -it openhab5 /bin/bash
```

## Aggiornamenti

### 5.0.3 > 5.1.3

Eseguito il 20260223. Sono stati necessari i seguenti passaggi:

* Rimuovere la strategia predefinita da tutti i file di configurazione della persistenza [perché deprecata](https://www.openhab.org/blog/2025-12-22-openhab-5-1-release.html#default-persistence-deprecated).
* Riavviare per ripristinare il funzionamento di alcuni dispositivi MQTT (tapparelle P1 e climatizzatore Camera 2 IR).
* Spegnere e riaccendere il termostato del soggiorno per correggere il timer, impostandolo a 5 minuti anziché 10.

## Appunti su Alpine

### SSH su Alpine

In caso di migrazione ad Alpine, considerare questo comando per installare SSH:

`apk add --update --no-cache openssh`

Restano da chiarire i seguenti punti:

* Come eseguire comandi all'avvio del container.
* Come viene mappata la directory `.ssh`.
* Se i pacchetti utilizzano gli stessi percorsi.
* Se alla fine tutto funziona davvero.

## Cronologia della migrazione dalla versione 2

### 20250710-1426: rimosso mqtt v1

```text
2025-07-10 14:23:41.323 [thome.event.ExtensionEvent] - Extension 'binding-mqtt1' has been uninstalled.
```

### 20250710-1508: rimosso exec v1

```text
2025-07-10 15:08:33.312 [thome.event.ExtensionEvent] - Extension 'binding-exec1' has been uninstalled.
```
