#!/bin/sh
#
#Script to keep ethernet buffers sized correctly to avoid error message in rx_uhd.
#Set as root crontab @reboot

sysctl -w net.core.wmem_max=500000000
sysctl -w net.core.rmem_max=500000000
sysctl -w net.core.wmem_default=500000000
sysctl -w net.core.rmem_default=500000000