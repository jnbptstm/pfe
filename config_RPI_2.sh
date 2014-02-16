#!/bin/bash

##############################################################################
# This script configure the interface of the Raspberry Pi num. 2 (the router)#
# This must be executed in su mode.                                          #
##############################################################################

echo Starting configuration...

# Network configuration
ifconfig wlan0 down
iwconfig wlan0 channel 1 essid Shared mode ad-hoc
ifconfig wlan0 up
ifconfig wlan0 192.168.1.3 netmask 255.255.255.0

# Adding HWaddr of the guardian to permit ping
arp -s 192.168.1.1 00:26:5E:30:C1:C1

# Adding HWaddr of the 2nd RPI to permit ping
arp -s 192.168.2.2 B8:27:EB:7E:15:22

# Adding default route:
route add default gw 192.168.1.1 wlan0

echo End of configuration.
