# Tiger Cloud Global Hack Week lab

Six hands-on exercises completed on a free shared Tiger Cloud development service,
using PostgreSQL 18.6 and TimescaleDB 2.30.2. All lab objects live in the
`mlh_ghw_2026` schema.

## Results

- Created `conditions` and inserted the three sensor-style rows from the
  [first hypertable guide](https://www.tigerdata.com/docs/build/how-to/your-first-hypertable).
- Simulated 1,156 readings across four sensors over 24 hours, following the
  [IoT tutorial](https://www.tigerdata.com/docs/learn/tutorials/simulate-iot-sensor-data).
- Created `sensor_hourly`, refreshed it, enabled real-time aggregation, and added
  an hourly refresh policy. Its reading count reconciles exactly with the source.
- Adapted the [financial ingestion tutorial](https://www.tigerdata.com/docs/learn/tutorials/ingest-real-time-financial-data)
  to [Kraken's public trade WebSocket](https://docs.kraken.com/api/docs/websocket-v2/trade/).
  Captured 50 recent trades and 10 actual live updates for BTC/USD; these are real
  market events, separate from the simulated IoT readings. See `financial-results.json`.
- Installed pgvector and pgvectorscale, generated real 384-dimensional
  `all-MiniLM-L6-v2` embeddings on the CPU, indexed them with HNSW, and performed
  cosine search with category and time filters. See `vector-results.json`.
- Configured Tiger MCP for a GitHub Copilot CLI session in read-only mode. The
  actual session transcript records service discovery and the database count query.

## Run

Create a fresh Tiger Cloud service and set `TIGER_DATABASE_URL` privately, or set
the usual PostgreSQL `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, and
`PGSSLMODE` environment variables. Credentials are excluded from this repository.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
python3 run_sql.py 01_hypertable_and_iot.sql
python3 run_sql.py 02_continuous_aggregate.sql
.venv/bin/python 03_financial_pipeline.py
.venv/bin/python 04_vector_search.py
```

Run the data-generation scripts once on a fresh schema. Each invocation appends
new samples. The financial listener exits after receiving live updates; no
background ingestion process is left running.

For [Tiger CLI and MCP](https://www.tigerdata.com/docs/get-started/quickstart/mcp-cli),
authenticate with `tiger auth login`, protect the service with
`tiger config set read_only all`, and use `mcp.example.json` as the client config.
The actual session used local private configuration and a database password
environment variable; neither credentials nor API keys are published.

`05_console_queries.sql` contains the queries used to verify the actual data in
the Tiger Console. Screenshots show real console results.
