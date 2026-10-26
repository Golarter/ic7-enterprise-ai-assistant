"""Persistencia de auditoría y estado simulado. No almacena secretos de herramientas."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


class AuditStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self._db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                question TEXT NOT NULL, answer TEXT NOT NULL,
                tools_used TEXT NOT NULL, sources TEXT NOT NULL,
                timestamp TEXT NOT NULL)''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id, timestamp)')

    def _db(self):
        return sqlite3.connect(str(self.path), timeout=10)

    def save(self, *, trace_id, session_id, question, answer, tools_used, sources):
        with self._db() as db:
            db.execute('INSERT INTO traces VALUES(?,?,?,?,?,?,?)', (
                trace_id, session_id, question, answer,
                json.dumps(tools_used, ensure_ascii=False),
                json.dumps(sources, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ))

    def history(self, session_id: str, limit=50):
        with self._db() as db:
            rows = db.execute('''SELECT trace_id, session_id, question, answer, tools_used, sources, timestamp
              FROM traces WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?''', (session_id, limit)).fetchall()
        return [{"trace_id": r[0], "session_id": r[1], "question": r[2], "answer": r[3],
                 "tools_used": json.loads(r[4]), "sources": json.loads(r[5]), "timestamp": r[6]} for r in rows]

    def count(self):
        with self._db() as db:
            return db.execute('SELECT count(*) FROM traces').fetchone()[0]


class RequestsStore:
    def __init__(self, path: Path):
        self.requests = {str(r['id']): r for r in json.loads(path.read_text(encoding='utf-8'))}

    def get(self, id_: str):
        return self.requests.get(id_)
