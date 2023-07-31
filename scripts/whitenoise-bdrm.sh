#!/bin/bash
pulseaudio --start
bluetoothctl connect DC:54:D7:03:FF:C9
mpg123 --loop -1 -q /opt/music/07-PinkNoise-dd-128kb.mp3
