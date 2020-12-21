#!/bin/bash

if [ "$1" = "on" ]; then
	curl -k 'https://172.27.72.145:10443/ajax/audio/set_config?type=9&data=%3CAudysseyLFC%3E1%3C%2FAudysseyLFC%3E&_=1608564593475' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0' -H 'Accept: text/plain, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-Requested-With: XMLHttpRequest' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://172.27.72.145:10443/audio/audio.html'

elif [ "$1" = "off" ]; then
	curl -k 'https://172.27.72.145:10443/ajax/audio/set_config?type=9&data=%3CAudysseyLFC%3E2%3C%2FAudysseyLFC%3E&_=1608564530925' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0' -H 'Accept: text/plain, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-Requested-With: XMLHttpRequest' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://172.27.72.145:10443/audio/audio.html'

else

	RESP=$(curl -s -k 'https://172.27.72.145:10443/ajax/audio/get_config?type=9' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0' -H 'Accept: text/plain, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-Requested-With: XMLHttpRequest' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://172.27.72.145:10443/audio/audio.html' | grep -o "AudysseyLFC.*" | cut -c25-25)

	if [ "$RESP" = "2" ] 
	then
		echo OFF
	fi

	if [ "$RESP" = "1" ] 
	then
		echo ON
	fi

fi
