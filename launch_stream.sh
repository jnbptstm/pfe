#!/bin/bash

raspivid -t 0 -w 480 -h 260 -fps 25 -b 800000 -p 0,0,640,480 -o - | gst-launch -v fdsrc ! h264parse ! rtph264pay config-interval=1 pt=96 ! gdppay ! tcpserversink host=192.168.1.2 port=5000
