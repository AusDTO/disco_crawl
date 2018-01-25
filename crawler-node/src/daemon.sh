#!/bin/bash
cd /src/
# let it be restarted every hour or two
# bash -c "sleep $(( ( RANDOM % 3600 ) + 3600 )); && pkill -9 -f python" &

while true;
do
    ./run.py  #  >/dev/null 2>/dev/null
    sleep 5  # let it rest a little
done
