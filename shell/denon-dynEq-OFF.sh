#!/bin/bash
curl -k 'https://172.27.72.145:10443/ajax/audio/set_config?type=9&data=%3CDynamicVolume%3E4%3C%2FDynamicVolume%3E&_=1608457501471' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0' -H 'Accept: text/plain, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-Requested-With: XMLHttpRequest' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://172.27.72.145:10443/audio/audio.html'

sleep 5

curl -k 'https://172.27.72.145:10443/ajax/audio/set_config?type=5&data=%3CRestorer%3E1%3C%2FRestorer%3E&_=1608468699858' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:83.0) Gecko/20100101 Firefox/83.0' -H 'Accept: text/plain, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'X-Requested-With: XMLHttpRequest' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Referer: https://172.27.72.145:10443/audio/audio.html'
