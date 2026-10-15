CREATE SCHEMA IF NOT EXISTS mlh_ghw_2026;
SET search_path TO mlh_ghw_2026, public;

CREATE TABLE IF NOT EXISTS conditions (
    time timestamptz NOT NULL,
    location text NOT NULL,
    device text NOT NULL,
    temperature double precision,
    humidity double precision
) WITH (tsdb.hypertable, tsdb.segmentby='device', tsdb.orderby='time DESC');

INSERT INTO conditions VALUES
    (now()-interval '2 hours', 'office', 'sensor-1', 22.1, 45.0),
    (now()-interval '1 hour', 'office', 'sensor-1', 22.3, 44.8),
    (now(), 'office', 'sensor-1', 22.2, 45.1);

CREATE TABLE IF NOT EXISTS sensors (
    id integer PRIMARY KEY,
    type varchar(50),
    location varchar(50)
);
INSERT INTO sensors VALUES
    (1,'a','floor'),(2,'a','ceiling'),(3,'b','floor'),(4,'b','ceiling')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS sensor_data (
    time timestamptz NOT NULL,
    sensor_id integer REFERENCES sensors(id),
    temperature double precision,
    cpu double precision
) WITH (tsdb.hypertable);

INSERT INTO sensor_data(time,sensor_id,temperature,cpu)
SELECT t, id, 18+random()*12, random()
FROM generate_series(now()-interval '24 hours',now(),interval '5 minutes') AS g(t)
CROSS JOIN generate_series(1,4) AS s(id);

SELECT hypertable_schema, hypertable_name, num_chunks
FROM timescaledb_information.hypertables
WHERE hypertable_schema='mlh_ghw_2026';
SELECT sensor_id,count(*) AS readings,round(avg(temperature)::numeric,2) AS avg_temp
FROM sensor_data GROUP BY sensor_id ORDER BY sensor_id;
