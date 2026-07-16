#!/bin/bash
set -e

# Wait for postgres to be ready
echo "Waiting for postgres..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "Postgres is ready!"

# Wait for redis to be ready
echo "Waiting for redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

# Start the application
exec "$@"
