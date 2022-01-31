#!/bin/bash
CURRENT_UID="$(id -u):$(id -g)"
export CURRENT_UID
docker-compose up -d