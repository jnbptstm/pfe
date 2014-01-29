#!/bin/bash

echo Starting configuration...

ifconfig eth0 down
ifconfig eth0 192.168.2.2 netmask 255.255.255.0

echo arp -s 192.168.1.1 00:26:5E:30:C1:C1
arp -s 192.168.2.1 B8:27:EB:2F:06:0F

route add default gw 192.168.2.2 eth0

ifconfig eth0 up

echo End of configuration

