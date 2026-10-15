SET search_path TO mlh_ghw_2026, public;
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour',time) AS bucket,sensor_id,
       avg(temperature) AS avg_temperature,
       min(temperature) AS min_temperature,
       max(temperature) AS max_temperature,
       avg(cpu) AS avg_cpu,count(*) AS reading_count
FROM sensor_data GROUP BY bucket,sensor_id
WITH NO DATA;

CALL refresh_continuous_aggregate('mlh_ghw_2026.sensor_hourly',NULL,NULL);
ALTER MATERIALIZED VIEW sensor_hourly SET (timescaledb.materialized_only=false);
SELECT add_continuous_aggregate_policy('mlh_ghw_2026.sensor_hourly',
    start_offset=>interval '24 hours',end_offset=>interval '1 hour',
    schedule_interval=>interval '1 hour',if_not_exists=>true);

SELECT bucket,sensor_id,round(avg_temperature::numeric,2) AS avg_temperature,
       reading_count FROM sensor_hourly ORDER BY bucket DESC,sensor_id LIMIT 8;
SELECT (SELECT sum(reading_count) FROM sensor_hourly) AS aggregate_readings,
       (SELECT count(*) FROM sensor_data) AS source_readings;
