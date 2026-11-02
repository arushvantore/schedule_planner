"""Shared sync runner for authorized academic source adapters.

Adapters are responsible for authenticating with their source and returning
normalized records. Credentials must stay in the platform's secret store or
environment, never in these academic content tables.
"""
from datetime import datetime, timezone
import hashlib
import json


class SourceAdapter:
    """Interface implemented by a college, Newton School, or Slack adapter."""

    provider = "unknown"

    def fetch_items(self):
        """Return normalized dictionaries for records the student may access."""
        raise NotImplementedError


def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _content_hash(item):
    keys = ("kind", "title", "subject", "chapter", "language",
            "event_date", "due_date", "url", "content")
    normalized = {key: item.get(key) for key in keys}
    encoded = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def sync_once(conn, connection_id, adapter):
    """Fetch one source snapshot, upsert changes, and persist sync health."""
    started_at = _timestamp()
    cursor = conn.execute(
        """INSERT INTO sync_runs (connection_id, started_at, status)
           VALUES (?, ?, 'running')""",
        (connection_id, started_at),
    )
    run_id = cursor.lastrowid
    conn.execute(
        "UPDATE source_connections SET last_attempt_at = ? WHERE id = ?",
        (started_at, connection_id),
    )
    try:
        items = adapter.fetch_items()
        changed = 0
        seen_at = _timestamp()
        for item in items:
            external_id = str(item["external_id"]).strip()
            title = str(item["title"]).strip()
            if not external_id or not title:
                continue
            digest = _content_hash(item)
            old = conn.execute(
                """SELECT content_hash FROM source_items
                   WHERE connection_id = ? AND external_id = ?""",
                (connection_id, external_id),
            ).fetchone()
            if old is None or old["content_hash"] != digest:
                changed += 1
            conn.execute(
                """INSERT INTO source_items
                   (connection_id, external_id, kind, title, subject, chapter,
                    language, event_date, due_date, url, content, content_hash, source_updated_at,
                    last_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(connection_id, external_id) DO UPDATE SET
                    kind=excluded.kind, title=excluded.title,
                    subject=excluded.subject, chapter=excluded.chapter,
                    language=excluded.language, event_date=excluded.event_date,
                    due_date=excluded.due_date, url=excluded.url,
                    content=excluded.content, content_hash=excluded.content_hash,
                    source_updated_at=excluded.source_updated_at,
                    last_seen_at=excluded.last_seen_at""",
                (connection_id, external_id, item.get("kind", "material"), title,
                 item.get("subject"), item.get("chapter"), item.get("language"),
                 item.get("event_date"), item.get("due_date"),
                 item.get("url"), item.get("content"), digest,
                 item.get("source_updated_at"), seen_at),
            )
        finished_at = _timestamp()
        conn.execute(
            """UPDATE sync_runs SET finished_at = ?, status = 'success',
               items_seen = ?, items_changed = ? WHERE id = ?""",
            (finished_at, len(items), changed, run_id),
        )
        conn.execute(
            """UPDATE source_connections SET status = 'connected',
               last_success_at = ?, last_error = NULL WHERE id = ?""",
            (finished_at, connection_id),
        )
        conn.commit()
        return {"status": "success", "items_seen": len(items),
                "items_changed": changed, "finished_at": finished_at}
    except Exception as exc:
        finished_at = _timestamp()
        error = str(exc)[:1000]
        conn.execute(
            """UPDATE sync_runs SET finished_at = ?, status = 'failed',
               error = ? WHERE id = ?""",
            (finished_at, error, run_id),
        )
        conn.execute(
            """UPDATE source_connections SET status = 'attention',
               last_error = ? WHERE id = ?""",
            (error, connection_id),
        )
        conn.commit()
        return {"status": "failed", "error": error,
                "finished_at": finished_at}
