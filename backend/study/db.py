"""SQLite storage for study data."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Iterator
from datetime import datetime, timezone
from pathlib import Path

from config_paths import get_data_dir


SCHEMA_VERSION = 1


def get_db_path() -> Path:
    data_dir = get_data_dir()
    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "study.sqlite3"
    fallback = Path(__file__).resolve().parent.parent.parent / "cache_data"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback / "study.sqlite3"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lemmas (
            lemma TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'known', 'ignored')),
            display TEXT,
            pos TEXT,
            level TEXT,
            glosses TEXT NOT NULL DEFAULT '[]',
            definition TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lemma TEXT NOT NULL,
            source_fragment TEXT NOT NULL,
            source_sentence TEXT NOT NULL,
            display TEXT,
            pos TEXT,
            level TEXT,
            glosses TEXT NOT NULL DEFAULT '[]',
            definition TEXT,
            source_fragment_translation TEXT,
            source_sentence_translation TEXT,
            study_line TEXT,
            csv_front TEXT,
            csv_back TEXT,
            due_at TEXT NOT NULL,
            interval_days INTEGER NOT NULL DEFAULT 1,
            ease REAL NOT NULL DEFAULT 2.5,
            repetitions INTEGER NOT NULL DEFAULT 0,
            lapses INTEGER NOT NULL DEFAULT 0,
            suspended INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(lemma, source_fragment)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
            rating TEXT NOT NULL CHECK (rating IN ('again', 'hard', 'good', 'easy')),
            interval_days INTEGER NOT NULL,
            ease REAL NOT NULL,
            xp_gained INTEGER NOT NULL,
            reviewed_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_cards_due_at ON cards(due_at, suspended);
        CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at ON reviews(reviewed_at);
        """
    )
    conn.execute("INSERT OR REPLACE INTO schema_meta(key, value) VALUES('version', ?)", (str(SCHEMA_VERSION),))
    _ensure_columns(conn)
    conn.commit()


def _ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(cards)").fetchall()}
    add_columns = [
        ("difficulty_score", "REAL NOT NULL DEFAULT 1.0"),
        ("frequency_in_text", "INTEGER NOT NULL DEFAULT 1"),
        ("reason", "TEXT NOT NULL DEFAULT 'Saved from your deck'"),
    ]
    for column, decl in add_columns:
        if column not in existing:
            conn.execute(f"ALTER TABLE cards ADD COLUMN {column} {decl}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
