from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Iterator
from uuid import uuid4

from app.core.config import PLATFORM_DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PlatformStore:
    def __init__(self, path: Path = PLATFORM_DB_PATH) -> None:
        self.path = path
        self._lock = RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            try:
                yield connection
                connection.commit()
            finally:
                connection.close()

    def _initialize(self) -> None:
        schema = """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS subscriptions (
          id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, status TEXT NOT NULL,
          provider TEXT NOT NULL, external_id TEXT UNIQUE, created_at TEXT NOT NULL,
          expires_at TEXT
        );
        CREATE TABLE IF NOT EXISTS manual_payments (
          id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, amount_xaf INTEGER NOT NULL,
          payer_phone TEXT NOT NULL, transaction_reference TEXT,
          status TEXT NOT NULL, created_at TEXT NOT NULL, verified_at TEXT,
          purpose TEXT NOT NULL DEFAULT 'subscription', user_id TEXT
        );
        CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, action TEXT NOT NULL,
          payload TEXT NOT NULL, risk TEXT NOT NULL, status TEXT NOT NULL,
          confirmation_required INTEGER NOT NULL, created_at TEXT NOT NULL,
          completed_at TEXT, result TEXT
        );
        CREATE TABLE IF NOT EXISTS notifications (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
          read INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS suggestions (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
          reason TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit_log (
          id TEXT PRIMARY KEY, event TEXT NOT NULL, detail TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS connector_permissions (
          connector TEXT PRIMARY KEY, access_mode TEXT NOT NULL,
          enabled INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cloud_objects (
          object_key TEXT PRIMARY KEY, size_bytes INTEGER NOT NULL,
          encrypted_size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, display_name TEXT NOT NULL,
          password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer',
          created_at TEXT NOT NULL, disabled_at TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY, user_id TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS wallet_transactions (
          id TEXT PRIMARY KEY, user_id TEXT NOT NULL, amount_xaf INTEGER NOT NULL,
          kind TEXT NOT NULL, description TEXT NOT NULL, reference TEXT UNIQUE,
          created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS usage_events (
          id TEXT PRIMARY KEY, user_id TEXT NOT NULL, service TEXT NOT NULL,
          units INTEGER NOT NULL, charge_xaf INTEGER NOT NULL, plan_id TEXT NOT NULL,
          created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_usage_user_created ON usage_events(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash);
        """
        with self.connection() as connection:
            connection.executescript(schema)
            connection.execute(
                "INSERT OR IGNORE INTO settings(key,value) VALUES('active_plan','core')"
            )
            connection.execute(
                "INSERT OR IGNORE INTO settings(key,value) VALUES('listening_mode','wake_phrase_only')"
            )
            for connector in ("google_calendar", "gmail", "google_drive"):
                connection.execute(
                    "INSERT OR IGNORE INTO connector_permissions VALUES(?,?,0,?)",
                    (connector, "read_only", utc_now()),
                )
            # Add account ownership to databases created by RC2. SQLite cannot
            # add the foreign key in place, but application-level checks fail closed.
            for table in ("subscriptions", "manual_payments"):
                columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
                if "user_id" not in columns:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT")
            for table in ("jobs", "notifications", "suggestions"):
                columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
                if "user_id" not in columns:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT")
            payment_columns = {row[1] for row in connection.execute("PRAGMA table_info(manual_payments)")}
            if "purpose" not in payment_columns:
                connection.execute("ALTER TABLE manual_payments ADD COLUMN purpose TEXT NOT NULL DEFAULT 'subscription'")

    def setting(self, key: str, default: str = "") -> str:
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def insert(self, table: str, values: dict[str, object]) -> str:
        allowed = {"jobs", "notifications", "suggestions", "audit_log", "subscriptions",
                   "manual_payments", "users", "sessions", "wallet_transactions", "usage_events"}
        if table not in allowed:
            raise ValueError("Unsupported table.")
        data = dict(values)
        data.setdefault("id", uuid4().hex)
        data.setdefault("created_at", utc_now())
        columns = ",".join(data)
        placeholders = ",".join("?" for _ in data)
        with self.connection() as connection:
            connection.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                tuple(json.dumps(v) if isinstance(v, (dict, list)) else v for v in data.values()),
            )
        return str(data["id"])

    def list_rows(self, table: str, limit: int = 50) -> list[dict[str, object]]:
        if table not in {"jobs", "notifications", "suggestions", "audit_log", "subscriptions",
                         "manual_payments", "users", "sessions", "wallet_transactions", "usage_events"}:
            raise ValueError("Unsupported table.")
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def update_job(self, job_id: str, status: str, result: str | None = None) -> bool:
        completed = utc_now() if status in {"completed", "failed", "cancelled"} else None
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE jobs SET status=?, result=?, completed_at=? WHERE id=?",
                (status, result, completed, job_id),
            )
        return cursor.rowcount == 1

    def list_user_rows(self, table: str, user_id: str, limit: int = 50) -> list[dict[str, object]]:
        if table not in {"jobs", "notifications", "suggestions"}:
            raise ValueError("Unsupported user table.")
        with self.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM {table} WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def claim_job(self) -> dict[str, object] | None:
        """Atomically claim the oldest queued task for the local worker."""
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            changed = connection.execute(
                "UPDATE jobs SET status='running' WHERE id=? AND status='queued'", (row["id"],)
            ).rowcount
            return dict(row) if changed == 1 else None


platform_store = PlatformStore()
