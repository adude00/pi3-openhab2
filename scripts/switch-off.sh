#!/bin/sh

/usr/bin/curl -s -X POST -d '{"id":1,"method":"Switch.SetConfig","params":{"id":0,"config":{"in_mode":"detached"}}}' http://172.27.72.39/rpc |jq
/usr/bin/curl -s -X POST -d '{"id":0, "method":"Switch.GetConfig", "params": { "id":0 }} }' http://172.27.72.39/rpc |jq

