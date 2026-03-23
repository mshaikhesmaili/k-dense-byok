from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# For MVP we store data locally in sandbox/ so everything stays on-device.
SANDBOX_ROOT = Path("sandbox").resolve()
DB_PATH = Path(os.environ.get("SCI_LITLAB_DB", str(SANDBOX_ROOT / "sci_litlab.db"))).resolve()


def _ensure_parent() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def connect():
    _ensure_parent()
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT,
                authors_json TEXT,
                journal TEXT,
                publication_year INTEGER,
                doi TEXT,
                pmid TEXT,
                abstract_text TEXT,
                file_path TEXT NOT NULL,
                raw_text TEXT,
                ingestion_status TEXT NOT NULL DEFAULT 'uploaded',
                extraction_status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS paper_sections (
                id TEXT PRIMARY KEY,
                paper_id TEXT NOT NULL,
                section_type TEXT,
                section_heading TEXT,
                section_order INTEGER,
                page_start INTEGER,
                page_end INTEGER,
                text TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(paper_id) REFERENCES papers(id) ON DELETE CASCADE
            );
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                paper_id TEXT NOT NULL,
                claim_text TEXT NOT NULL,
                claim_type TEXT,
                evidence_type TEXT,
                supporting_section_id TEXT,
                supporting_excerpt TEXT,
                overclaim_risk TEXT,
                confidence_score REAL,
                review_status TEXT NOT NULL DEFAULT 'unreviewed',
                review_note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(paper_id) REFERENCES papers(id) ON DELETE CASCADE
            );
            """
        )


# Initialize on import so API works out-of-the-box.
init_db()
