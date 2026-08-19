from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parents[2] / "certificate_ocr.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                average_confidence REAL,
                fields_json TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_document(record: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents
            (id, filename, page_count, average_confidence, fields_json, raw_text, stored_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["filename"],
                record["page_count"],
                record.get("average_confidence"),
                json.dumps(record["fields"], ensure_ascii=False),
                record["raw_text"],
                record["stored_path"],
                record["created_at"],
            ),
        )
        conn.commit()


def get_document(document_id: str) -> Optional[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "filename": row["filename"],
        "page_count": row["page_count"],
        "average_confidence": row["average_confidence"],
        "fields": json.loads(row["fields_json"]),
        "raw_text": row["raw_text"],
        "stored_path": row["stored_path"],
        "created_at": row["created_at"],
    }


def list_documents(limit: int = 20) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, filename, page_count, average_confidence, fields_json, created_at FROM documents ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "filename": row["filename"],
            "page_count": row["page_count"],
            "average_confidence": row["average_confidence"],
            "fields": json.loads(row["fields_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def delete_document(document_id: str) -> Optional[str]:
    doc = get_document(document_id)
    if not doc:
        return None
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.commit()
    return doc.get("stored_path")
