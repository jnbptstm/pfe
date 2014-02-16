#!/bin/bash

echo Starting configuration...

# Network configuration
ifconfig eth1 down
iwconfig eth1 mode ad-hoc
iwconfig eth1 channel 1
iwconfig eth1 essid "Shared"
ifconfig eth1 up
ifconfig eth1 192.168.1.1 netmask 255.255.255.0

# DHCP configuration
dnsmasq -i eth1 -F 192.168.1.1,192.168.1.100 -O option:router,192.168.1.1

# Routing configuration
sysctl -w net.ipv4.ip_forward=1
iptables -A FORWARD -i eth1 -s 192.168.1.0/255.255.255.0 -o eth0 -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

echo End of configuration

# Nameserver has been added in /etc/resolv.conf (10.188.0.1) -- should be changed, depending on network...

# If port n.53 is already used by another process, locate this process:
# sudo netstat -anlp | grep -w LISTEN
# Kill process: sudo kill -9 ...
