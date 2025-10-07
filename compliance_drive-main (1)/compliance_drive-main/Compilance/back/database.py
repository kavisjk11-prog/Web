# backend/database.py
import os
import sqlite3
import json
from typing import Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DATA_DIR, "scenarios.db")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def get_conn():
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_name TEXT,
        inputs TEXT,
        results TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def insert_scenario(scenario_name: str, inputs: Dict[str, Any], results: Dict[str, Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scenarios (scenario_name, inputs, results) VALUES (?, ?, ?)",
        (scenario_name, json.dumps(inputs), json.dumps(results))
    )
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def list_scenarios():
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT id, scenario_name, created_at FROM scenarios ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_scenario_by_id(scenario_id: int):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_scenario_by_id(scenario_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0
