#!/bin/bash
#This is called by the cron job. Sets up environment and runs job
export $(cat /src/crawler.env | xargs)
env | grep CRAWL_
cd /src; /usr/local/bin/node /src/crawl.js --fliporder --logfile /src/logs/flipcrawl
