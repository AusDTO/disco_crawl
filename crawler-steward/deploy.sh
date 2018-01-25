#!/bin/bash
echo "Starting deploy to $1"
export TARGET_ROOT="/opt/webindex-steward"

ssh $1 "sudo mkdir -p ${TARGET_ROOT}; sudo chown -R ubuntu ${TARGET_ROOT}"

rsync -L --delete --recursive --exclude 'var' \
      --exclude '.venv' --exclude '.git' \
      src webindex-steward.env Dockerfile .dockerignore docker-compose.yml src \
      $1:${TARGET_ROOT}

echo "Finished deploy to $1"
