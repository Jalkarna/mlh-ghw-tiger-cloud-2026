"""Run the lab's SQL without putting connection secrets into arguments or logs."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import os
import subprocess
import sys

def pg_environment():
    env = os.environ.copy()
    private_file = Path(__file__).parent.parent / '.tiger-dsn-private'
    raw = env.get('TIGER_DATABASE_URL')
    if raw is None and private_file.exists():
        raw = private_file.read_text().strip()
    if not raw:
        env.setdefault('PGSSLMODE', 'require')
        env.setdefault('PGCONNECT_TIMEOUT', '15')
        return env
    uri = urlsplit(raw)
    env.update(PGHOST=uri.hostname, PGPORT=str(uri.port or 5432),
               PGDATABASE=uri.path.lstrip('/'), PGUSER=unquote(uri.username),
               PGPASSWORD=unquote(uri.password or ''), PGSSLMODE='require',
               PGCONNECT_TIMEOUT='15')
    return env

if __name__ == '__main__':
    result = subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','-P','pager=off'],
                            input=Path(sys.argv[1]).read_text(), text=True,
                            env=pg_environment(), capture_output=True)
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)
