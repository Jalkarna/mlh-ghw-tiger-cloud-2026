"""Create real MiniLM embeddings and query them with time and category filters."""
import json
import os
from pathlib import Path

from fastembed import TextEmbedding
import psycopg

from run_sql import pg_environment

DOCUMENTS=[
 ('sensor-alert','iot','Temperature sensor readings can detect overheating equipment.'),
 ('sensor-metrics','iot','Hourly sensor averages summarize temperature and CPU utilization.'),
 ('database','iot','A hypertable partitions timestamped measurements into time chunks.'),
 ('soccer','campus','The campus soccer club practices teamwork and ball skills.'),
 ('markets','finance','Live Bitcoin trades arrive through a cryptocurrency exchange feed.'),
 ('art','campus','The painting workshop teaches watercolor and visual composition.'),
]
QUERY='How can I monitor equipment temperature and detect heat problems?'

def main():
    model=TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2',
                        cache_dir='.cache/embeddings',threads=2)
    embeddings=list(model.embed([d[2] for d in DOCUMENTS]))
    query=list(model.embed([QUERY]))[0]
    assert len(query)==384
    for k,v in pg_environment().items():
        if k.startswith('PG'): os.environ[k]=v
    with psycopg.connect('') as conn:
        conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        conn.execute('CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE')
        conn.execute('''CREATE TABLE IF NOT EXISTS mlh_ghw_2026.activity_embeddings (
          time timestamptz NOT NULL, document_id text NOT NULL, category text NOT NULL,
          content text NOT NULL, embedding vector(384) NOT NULL
        ) WITH (tsdb.hypertable,tsdb.segmentby='category')''')
        for (id,category,text),embedding in zip(DOCUMENTS,embeddings):
            vector=json.dumps(embedding.tolist())
            conn.execute('INSERT INTO mlh_ghw_2026.activity_embeddings VALUES (now(),%s,%s,%s,%s::vector)',
                         (id,category,text,vector))
        conn.execute('CREATE INDEX IF NOT EXISTS activity_embedding_cosine_idx ON mlh_ghw_2026.activity_embeddings USING hnsw (embedding vector_cosine_ops)')
        conn.execute('''CREATE TABLE IF NOT EXISTS mlh_ghw_2026.search_queries (
          id text PRIMARY KEY,question text NOT NULL,embedding vector(384) NOT NULL)''')
        conn.execute('''INSERT INTO mlh_ghw_2026.search_queries VALUES (%s,%s,%s::vector)
          ON CONFLICT (id) DO UPDATE SET question=EXCLUDED.question,embedding=EXCLUDED.embedding''',
          ('equipment-heat',QUERY,json.dumps(query.tolist())))
        rows=conn.execute('''SELECT document_id,category,round((1-(embedding <=> %s::vector))::numeric,4) AS similarity
            FROM mlh_ghw_2026.activity_embeddings
            WHERE time>=now()-interval '7 days' AND category='iot'
            ORDER BY embedding <=> %s::vector LIMIT 3''',
            (json.dumps(query.tolist()),json.dumps(query.tolist()))).fetchall()
        assert rows and rows[0][0]=='sensor-alert'
        report={'model':'sentence-transformers/all-MiniLM-L6-v2','dimensions':384,
                'documents':len(DOCUMENTS),'query':QUERY,'time_filter':'last 7 days',
                'metadata_filter':{'category':'iot'},'distance':'cosine',
                'results':[{'document_id':r[0],'category':r[1],'similarity':float(r[2])} for r in rows]}
        conn.commit()
        Path('vector-results.json').write_text(json.dumps(report,indent=2)+'\n')
        Path('vector-query.json').write_text(json.dumps(query.tolist()))
        print(json.dumps(report,indent=2))

if __name__=='__main__': main()
