#!/bin/bash
echo "Starting deploy to $1"
export TARGET_ROOT="/opt/crawler-3"

ssh $1 "sudo mkdir -p ${TARGET_ROOT}; sudo chown -R ubuntu ${TARGET_ROOT}"

# scp -r src/ crawler-node.env Dockerfile docker-compose.yml $1:/opt/crawler-node/

rsync -L --delete --recursive --exclude 'var' \
      --exclude '.venv' --exclude '.git' \
      src webindex-crawler-node.env manage.sh Dockerfile .dockerignore docker-compose.yml src \
      $1:${TARGET_ROOT}

echo "Finished deploy to $1"
