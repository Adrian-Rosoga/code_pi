#!/bin/sh

now=$(date +%F_%T)

now=$(date +%F_%T)

ps aux --sort -rss | tee -a pi_snapshot_${now}.txt

echo "" | tee -a pi_snapshot_${now}.txt

free -h | tee -a pi_snapshot_${now}.txt

