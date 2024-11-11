#!/bin/bash

echo "PostgreSQL container starting with user: $POSTGRES_USER, db: $POSTGRES_DB"

# Run the PostgreSQL container
docker run --name postgres-dev \
  -e POSTGRES_USER=$POSTGRES_USER \
  -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  -e POSTGRES_DB=$POSTGRES_DB \
  -p $POSTGRES_PORT:5432 \
  -d $POSTGRES_IMAGE

echo "PostgreSQL container started with user: $POSTGRES_USER, db: $POSTGRES_DB"
