#!/bin/sh
echo "Aguardando PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL está pronto!"
exec flask run --host=0.0.0.0 --port=5000