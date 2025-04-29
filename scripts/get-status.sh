# appunti shelly api

curl -s -X POST -d '{"id":0, "method":"Switch.GetConfig", "params": { "id":0 }} }' http://172.27.72.39/rpc |jq

curl -s -X POST -d '{"id":0, "src":"user_1", "method":"Switch.Set", "params": {"id":0, "on":true}}}' http://172.27.72.39/rpc |jq

curl -s -X POST -d '{"id":0, "src":"user_1", "method":"Switch.Set", "params": {"id":0, "on":false}}}' http://172.27.72.39/rpc |jq


in_mode

http://172.27.72.39/rpc/Switch.GetConfig?id=0 |jq


curl -s -X POST -d '{"id":1,"method":"Switch.SetConfig","params":{"id":0,"config":{"in_mode":"detached"}}}' http://172.27.72.39/rpc |jq
curl -s -X POST -d '{"id":1,"method":"Switch.SetConfig","params":{"id":0,"config":{"in_mode":"flip"}}}' http://172.27.72.39/rpc |jq

