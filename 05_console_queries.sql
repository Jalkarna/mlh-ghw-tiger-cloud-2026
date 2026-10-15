-- Hypertables: actual TimescaleDB catalog metadata.
SELECT hypertable_name, num_chunks
FROM timescaledb_information.hypertables
WHERE hypertable_schema='mlh_ghw_2026'
ORDER BY hypertable_name;

-- Simulated IoT data: four sensors, 289 readings each.
SELECT count(*) AS readings, count(DISTINCT sensor_id) AS sensors
FROM mlh_ghw_2026.sensor_data;

-- Reconcile the hourly aggregate with its source data.
SELECT count(*) AS hourly_groups, sum(reading_count) AS readings
FROM mlh_ghw_2026.sensor_hourly;

-- Real financial trade ingestion; source is the live Kraken public WebSocket.
SELECT count(*) AS trades, max(time) AS latest_trade
FROM mlh_ghw_2026.crypto_ticks;

-- Hybrid similarity search: semantic vector, time range, and metadata.
SELECT d.document_id,
       round((1-(d.embedding <=> q.embedding))::numeric,4) AS similarity
FROM mlh_ghw_2026.activity_embeddings d
CROSS JOIN mlh_ghw_2026.search_queries q
WHERE q.id='equipment-heat' AND d.category='iot'
  AND d.time>=now()-interval '7 days'
ORDER BY d.embedding <=> q.embedding LIMIT 3;
