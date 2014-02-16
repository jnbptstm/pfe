#!/bin/bash

################################################################################
# This script configure the interface of the Raspberry Pi num. 1 (with camera) #
# This must be executed in su mode.                                            #
################################################################################

echo Starting configuration...

ifconfig eth0 down
ifconfig eth0 192.168.2.2 netmask 255.255.255.0

arp -s 192.168.2.1 B8:27:EB:2F:06:0F

route add default gw 192.168.2.2 eth0

ifconfig eth0 up

echo End of configuration

