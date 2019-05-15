#!/bin/bash

# Giorgio
GIORGIO=$(l2ping 00:18:16:11:FF:94 -c 2 |grep time |wc -l)

if l2ping 10:18:16:11:FF:94 -c 1 > /dev/null ; then
  echo Giorgio PRESENTE
else
  echo Giorgio ASSENTE
fi
