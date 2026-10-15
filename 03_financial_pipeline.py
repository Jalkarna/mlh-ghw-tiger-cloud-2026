"""Ingest actual public Kraken BTC/USD WebSocket trades into Tiger Cloud."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import os
import time

import psycopg
import websockets

from run_sql import pg_environment

DDL = """
CREATE TABLE IF NOT EXISTS mlh_ghw_2026.crypto_ticks (
  time timestamptz NOT NULL, symbol text NOT NULL, trade_id bigint NOT NULL,
  price numeric NOT NULL, quantity numeric NOT NULL, side text,
  source text NOT NULL, UNIQUE(time,symbol,trade_id)
) WITH (tsdb.hypertable,tsdb.segmentby='symbol');
"""

async def main():
    env=pg_environment()
    for key,value in env.items():
        if key.startswith('PG'): os.environ[key]=value
    with psycopg.connect('') as conn:
        conn.execute(DDL)
        conn.commit()
        started=time.monotonic()
        snapshots=updates=0
        async with websockets.connect('wss://ws.kraken.com/v2',open_timeout=20) as ws:
            await ws.send(json.dumps({'method':'subscribe','params':{
                'channel':'trade','symbol':['BTC/USD'],'snapshot':True}}))
            while time.monotonic()-started<45:
                try:
                    message=json.loads(await asyncio.wait_for(ws.recv(),timeout=12))
                except asyncio.TimeoutError:
                    if updates: break
                    continue
                if message.get('channel')!='trade': continue
                if message.get('type')=='snapshot': snapshots+=len(message['data'])
                else: updates+=len(message['data'])
                rows=[(t['timestamp'],t['symbol'],t['trade_id'],t['price'],t['qty'],t['side'],'Kraken WebSocket v2') for t in message['data']]
                with conn.cursor() as cur:
                    cur.executemany('INSERT INTO mlh_ghw_2026.crypto_ticks VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',rows)
                conn.commit()
                if updates>=10: break
        total=conn.execute('SELECT count(*),min(time),max(time) FROM mlh_ghw_2026.crypto_ticks').fetchone()
        assert updates>0, 'No live updates received; do not claim real-time ingestion'
        report={'source':'wss://ws.kraken.com/v2','symbol':'BTC/USD',
                'captured_at':datetime.now(timezone.utc).isoformat(),
                'snapshot_events':snapshots,'live_update_events':updates,
                'database_rows':total[0],'earliest_trade':str(total[1]),'latest_trade':str(total[2])}
        Path('financial-results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))

if __name__=='__main__': asyncio.run(main())
