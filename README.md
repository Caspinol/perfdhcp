# perfDHCP
______

## Description

A simple DHCPv4 tester using the pydhcplib. It supports broadcast and unicast server
discoveries. When the "-m x" option is specified it generate x random mac addresses:

__perfDHCP -m 10 -s 255.255.255.255__

You can pre generate MAC addresses and store them in a file:

__perfDHCP -m 10 > mac_list.txt__

in case you need to allow them on a RADIUS server beforehand. Then jus load them:

__cat mac_list.txt | perfDHCP -s 255.255.255.255__

## Usage
```
perfDHCP -m 10 -s 255.255.255.255
	or
cat mac_list.txt | perfDHCP -s 255.255.255.255
	or
perfDHCP -m 10 > mac_list.txt

optional arguments:
  -h, --help            show this help message and exit
  --macgen x, -m x      Generate "x" random mac addresses
  --server x.x.x.x, -s x.x.x.x
                        DHCP server to test or '255.255.255.255' for broadcast
  --workers x, -w x     Number of workers (default: CPU count)
```

## TODO:

* Improve the listener.
* Add should be able to bind to interface.
