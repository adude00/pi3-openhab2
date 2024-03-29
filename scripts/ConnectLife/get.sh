#!/bin/bash
MYDIR="$(dirname "$(which "$0")")"
source $MYDIR/bearer.sh

echo BEARER: $BEARER

GIOCHI=8650051000200030003000000f7f60c2690d-8650051000200030003000000f7f60c2690d
OFFICINA=8650051000200030003000000f7f60bc1a3a-8650051000200030003000000f7f60bc1a3a


APPLIANCES=https://api.connectlife.io/api/v1/appliance
GIOCHI_METADATA=https://api.connectlife.io/api/v1/appliance/metadata/8650051000200030003000000f7f60c2690d-8650051000200030003000000f7f60c2690d/en
GIOCHI_PROFILE=https://api.connectlife.io/api/v1/appliance/profile/8650051000200030003000000f7f60c2690d-8650051000200030003000000f7f60c2690d
GIOCHI_STATUS=https://api.connectlife.io/api/v1/appliance/8650051000200030003000000f7f60c2690d-8650051000200030003000000f7f60c2690d
OFFICINA_STATUS=https://api.connectlife.io/api/v1/appliance/8650051000200030003000000f7f60bc1a3a-8650051000200030003000000f7f60bc1a3a

URL=$GIOCHI_STATUS
URL=$OFFICINA_STATUS

curl -s -X 'GET' \
  $URL \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer '"$BEARER" |jq 
