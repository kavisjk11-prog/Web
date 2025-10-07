from db import get_db
import json

def save_scenario(data):
    conn = get_db()
    conn.execute(
        "INSERT INTO scenarios (scenario_name, inputs, results) VALUES (?, ?, ?)",
        (data["scenario_name"], json.dumps(data.get("inputs", {})), json.dumps(data.get("results", {})))
    )
    conn.commit()
    conn.close()

def get_all_scenarios():
    conn = get_db()
    rows = conn.execute("SELECT * FROM scenarios").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_scenario(scenario_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}

def delete_scenario(scenario_id):
    conn = get_db()
    conn.execute("DELETE FROM scenarios WHERE id=?", (scenario_id,))
    conn.commit()
    conn.close()
