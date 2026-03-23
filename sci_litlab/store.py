from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from sci_litlab.db import connect
from sci_litlab.models import MinimalExtractionResult, now_iso


def _uuid() -> str:
    return str(uuid.uuid4())


def create_paper(file_path: str) -> str:
    paper_id = _uuid()
    ts = now_iso()
    with connect() as con:
        con.execute(
            """
            INSERT INTO papers (
              id, file_path, ingestion_status, extraction_status, created_at, updated_at
            ) VALUES (?, ?, 'uploaded', 'pending', ?, ?)
            """,
            (paper_id, file_path, ts, ts),
        )
    return paper_id


def list_papers(q: str | None = None, limit: int = 50, offset: int = 0):
    with connect() as con:
        if q:
            like = f"%{q}%"
            rows = con.execute(
                """
                SELECT id, title, publication_year, journal, doi, created_at, ingestion_status, extraction_status
                FROM papers
                WHERE title LIKE ? OR doi LIKE ? OR journal LIKE ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (like, like, like, limit, offset),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT id, title, publication_year, journal, doi, created_at, ingestion_status, extraction_status
                FROM papers
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
    return [dict(r) for r in rows]


def get_paper(paper_id: str) -> dict | None:
    with connect() as con:
        row = con.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
        return dict(row) if row else None


def update_paper_fields(paper_id: str, fields: dict):
    if not fields:
        return
    fields = dict(fields)
    fields["updated_at"] = now_iso()

    cols = ", ".join([f"{k}=?" for k in fields.keys()])
    vals = list(fields.values())
    vals.append(paper_id)

    with connect() as con:
        con.execute(f"UPDATE papers SET {cols} WHERE id=?", vals)


def delete_paper(paper_id: str) -> None:
    with connect() as con:
        con.execute("DELETE FROM papers WHERE id=?", (paper_id,))


def upsert_sections(paper_id: str, sections: list[dict]) -> None:
    ts = now_iso()
    with connect() as con:
        con.execute("DELETE FROM paper_sections WHERE paper_id=?", (paper_id,))
        for s in sections:
            con.execute(
                """
                INSERT INTO paper_sections (
                  id, paper_id, section_type, section_heading, section_order, page_start, page_end, text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _uuid(),
                    paper_id,
                    s.get("section_type"),
                    s.get("section_heading"),
                    s.get("section_order"),
                    s.get("page_start"),
                    s.get("page_end"),
                    s.get("text"),
                    ts,
                ),
            )


def list_sections(paper_id: str) -> list[dict]:
    with connect() as con:
        rows = con.execute(
            """
            SELECT id, paper_id, section_type, section_heading, section_order, page_start, page_end, text, created_at
            FROM paper_sections
            WHERE paper_id=?
            ORDER BY section_order ASC
            """,
            (paper_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def create_claim(paper_id: str, claim_text: str, supporting_section_id: str | None = None, supporting_excerpt: str | None = None):
    ts = now_iso()
    with connect() as con:
        con.execute(
            """
            INSERT INTO claims (
              id, paper_id, claim_text, supporting_section_id, supporting_excerpt,
              overclaim_risk, confidence_score, review_status, created_at
            ) VALUES (?, ?, ?, ?, ?, 'unknown', NULL, 'unreviewed', ?)
            """,
            (_uuid(), paper_id, claim_text, supporting_section_id, supporting_excerpt, ts),
        )


def list_claims(paper_id: str) -> list[dict]:
    with connect() as con:
        rows = con.execute(
            """
            SELECT * FROM claims WHERE paper_id=? ORDER BY created_at DESC
            """,
            (paper_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def patch_claim(paper_id: str, claim_id: str, fields: dict) -> dict | None:
    allowed = {"review_status", "review_note", "overclaim_risk", "confidence_score"}
    fields = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not fields:
        return get_claim(paper_id, claim_id)

    cols = ", ".join([f"{k}=?" for k in fields.keys()])
    vals = list(fields.values())
    vals.extend([claim_id, paper_id])

    with connect() as con:
        con.execute(
            f"UPDATE claims SET {cols} WHERE id=? AND paper_id=?",
            vals,
        )
    return get_claim(paper_id, claim_id)


def get_claim(paper_id: str, claim_id: str) -> dict | None:
    with connect() as con:
        row = con.execute(
            "SELECT * FROM claims WHERE id=? AND paper_id=?",
            (claim_id, paper_id),
        ).fetchone()
    return dict(row) if row else None
