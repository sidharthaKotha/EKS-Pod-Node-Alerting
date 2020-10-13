#!/bin/bash
touch events.txt
while true
do
 nohup python3 test2.py & # change name of your python file
 sleep 5
done
