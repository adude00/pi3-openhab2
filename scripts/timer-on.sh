#!/bin/sh

# SET
/usr/bin/curl -s -X POST -d '{"id":1,"method":"Switch.SetConfig","params":{"id":0,"config":{"auto_off":true}}}' http://172.27.72.38/rpc |jq

# STATUS
/usr/bin/curl -s -X POST -d '{"id":0, "method":"Switch.GetConfig", "params": { "id":0 }} }' http://172.27.72.38/rpc |jq
