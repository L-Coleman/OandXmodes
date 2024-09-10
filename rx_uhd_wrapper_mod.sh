#!/bin/bash

sudo sysctl -w net.core.wmem_max=500000000
sudo sysctl -w net.core.rmem_max=500000000
sudo sysctl -w net.core.wmem_default=500000000
sudo sysctl -w net.core.rmem_default=500000000

