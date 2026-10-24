import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config import DATABASE_PATH

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[Path] = None) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                extracted_path TEXT NOT NULL,
                file_count INTEGER NOT NULL DEFAULT 0,
                detected_tech TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'ready'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                change_type TEXT NOT NULL,
                change_payload TEXT NOT NULL,
                report_data TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

# Project DB operations
def insert_project(
    project_id: str,
    name: str,
    extracted_path: str,
    file_count: int,
    detected_tech: Dict[str, Any],
    status: str = "ready",
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    tech_json = json.dumps(detected_tech)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (id, name, created_at, extracted_path, file_count, detected_tech, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, name, now, extracted_path, file_count, tech_json, status),
        )
        conn.commit()
    return {
        "id": project_id,
        "name": name,
        "created_at": now,
        "extracted_path": extracted_path,
        "file_count": file_count,
        "detected_tech": detected_tech,
        "status": status,
    }

def get_projects(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "extracted_path": row["extracted_path"],
                "file_count": row["file_count"],
                "detected_tech": json.loads(row["detected_tech"]),
                "status": row["status"],
            })
        return result

def get_project_by_id(project_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "created_at": row["created_at"],
            "extracted_path": row["extracted_path"],
            "file_count": row["file_count"],
            "detected_tech": json.loads(row["detected_tech"]),
            "status": row["status"],
        }

def delete_project_record(project_id: str, db_path: Optional[Path] = None) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0

# Report DB operations
def insert_report(
    report_id: str,
    project_id: str,
    change_type: str,
    change_payload: Dict[str, Any],
    report_data: Dict[str, Any],
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reports (id, project_id, created_at, change_type, change_payload, report_data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                project_id,
                now,
                change_type,
                json.dumps(change_payload),
                json.dumps(report_data),
            ),
        )
        conn.commit()
    return {
        "id": report_id,
        "project_id": project_id,
        "created_at": now,
        "change_type": change_type,
        "change_payload": change_payload,
        "report_data": report_data,
    }

def get_reports_by_project(project_id: str, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM reports WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "project_id": row["project_id"],
                "created_at": row["created_at"],
                "change_type": row["change_type"],
                "change_payload": json.loads(row["change_payload"]),
                "report_data": json.loads(row["report_data"]),
            })
        return result

def get_report_by_id(report_id: str, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "created_at": row["created_at"],
            "change_type": row["change_type"],
            "change_payload": json.loads(row["change_payload"]),
            "report_data": json.loads(row["report_data"]),
        }
