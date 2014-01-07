# Configuration du réseau : 
ifconfig eth1 down
iwconfig eth1 mode ad-hoc
iwconfig eth1 channel 1
# iwconfig wlan0 key 1234567890
iwconfig eth1 essid Shared
ifconfig eth1 up
ifconfig eth1 192.168.1.1 netmask 255.255.255.0
# Configuration DHCP :
dnsmasq -i eth1 -F 192.168.1.1,192.168.1.100 -O option:router,192.168.1.1
# Configuration du routage :
sysctl -w net.ipv4.ip_forward=1
iptables -A FORWARD -i eth1 -s 192.168.1.0/255.255.255.0 -o eth0 -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE


# Si le port 53 est déjà utilisé, localiser le processus qui l'utilise:
# sudo netstat -anlp | grep -w LISTEN
# Tuer ce processus: sudo kill ...
