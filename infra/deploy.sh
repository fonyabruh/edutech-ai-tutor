#!/bin/bash
set -e

REMOTE=${REMOTE:-"user@your-vm-ip"}
DIR="/opt/edutech"

rsync -az --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='node_modules' --exclude='.expo' \
  "$(dirname "$0")/../backend" "$REMOTE:$DIR/"

rsync -az "$(dirname "$0")/../infra/." "$REMOTE:$DIR/infra/"

ssh "$REMOTE" "cd $DIR/infra && docker compose pull && docker compose up -d --build"
echo "\ndeploy done"
