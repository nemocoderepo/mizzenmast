#!/bin/bash

for i in {1..100}; do
        date +%Y%m%d%H%M%S%N
        hcitool rssi $1
done
