#!/bin/bash
set -e

echo "Waiting for Kafka to be ready..."

for i in {1..30}; do
  if kafka-topics --bootstrap-server kafka:9092 --list > /dev/null 2>&1; then
    echo "Kafka is ready!"
    break
  fi
  echo "Kafka not ready yet... retrying in 2s ($i/30)"
  sleep 2
done

echo "Creating topic: device_streams (if missing)"
kafka-topics --create \
  --topic device_streams \
  --bootstrap-server kafka:9092 \
  --partitions 1 \
  --replication-factor 1 \
  || echo "Topic 'device_streams' already exists."

echo "Kafka initialization complete."
