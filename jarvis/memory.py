import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _utc_now():
    return datetime.now(timezone.utc)


@dataclass
class Fragment:
    id: int
    text: str
    source: str
    created_at: str


class FragmentStore:
    def __init__(self, path):
        mkdir = path.rsplit("/", 1)[0]
        import os
        if mkdir and mkdir != path:
            os.makedirs(mkdir, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fragments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_fragments_created ON fragments (created_at)"
            )
            self._conn.commit()

    def write(self, text, source):
        text = text.strip()
        if not text:
            return None
        fragment = Fragment(
            id=0,
            text=text,
            source=source,
            created_at=_now(),
        )
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO fragments (text, source, created_at) VALUES (?, ?, ?)",
                (fragment.text, fragment.source, fragment.created_at),
            )
            self._conn.commit()
            fragment.id = cur.lastrowid
        return fragment

    def recent(self, limit=10):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM fragments ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Fragment(r["id"], r["text"], r["source"], r["created_at"]) for r in rows]

    def search(self, query, limit=10):
        terms = [t for t in str(query).lower().split() if len(t) > 2]
        if not terms:
            return self.recent(limit)
        where = " AND ".join("lower(text) LIKE ?" for _ in terms)
        params = ["%" + t + "%" for t in terms]
        with self._lock:
            rows = self._conn.execute(
                f"SELECT * FROM fragments WHERE {where} ORDER BY id DESC LIMIT ?",
                params + [limit],
            ).fetchall()
        return [Fragment(r["id"], r["text"], r["source"], r["created_at"]) for r in rows]

    def count(self):
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS c FROM fragments").fetchone()
        return int(row["c"])

    def searches_for(self, query, limit=5):
        terms = [t for t in str(query).lower().split() if len(t) > 2]
        if not terms:
            return []
        where = " OR ".join("lower(text) LIKE ?" for _ in terms)
        params = ["%" + t + "%" for t in terms]
        with self._lock:
            rows = self._conn.execute(
                f"SELECT * FROM fragments WHERE {where} ORDER BY id DESC LIMIT ?",
                params + [limit],
            ).fetchall()
        return [Fragment(r["id"], r["text"], r["source"], r["created_at"]) for r in rows]

    def close(self):
        with self._lock:
            self._conn.close()