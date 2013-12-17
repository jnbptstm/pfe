#!/bin/bash

##################################################################
# This script configure the interface of the Raspberry Pi num. 2 #
# This must be executed in su mode.                              #
# -------------------------------------------------------------- #
# TODO: making this configuration file generic.                  #
##################################################################

echo Starting configuration...

ifconfig wlan0 down
iwconfig wlan0 channel 1 essid pfe_network mode ad-hoc
ifconfig wlan0 up
ifconfig wlan0 192.168.1.3 netmask 255.255.255.0

# Adding HWaddr of the 2nd RPI to permit ping:
arp -s 192.168.1.3 80:1F:02:A6:A5:D8

echo End of configuration.
