#!/bin/sh
# Docker compose for the PDI stack: ./pdi.sh up -d | ./pdi.sh logs celery-worker | ./pdi.sh down
cd "$(dirname "$0")" && exec docker compose --env-file .env.pdi -p barqpdi -f docker-compose.yml -f docker-compose.pdi.yml "$@"
