from database.db import get_connection


# ---------------- INSERTS ----------------

INSERT_SQL = """
INSERT INTO lab_interpretations (
    subject_id,
    hadm_id,
    test_name,
    value,
    unit,
    gender,
    status,
    reason,
    processed_time,
    reviewed
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def insert_lab_results_bulk(records: list[tuple]):
    """
    Bulk insert lab interpretations.
    Used during ingestion / preprocessing (FAST).
    """
    if not records:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(INSERT_SQL, records)
    conn.commit()
    conn.close()


def clear_lab_interpretations():
    """
    ⚠️ DEVELOPMENT ONLY
    Clears all lab interpretations.
    DO NOT call this in production.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lab_interpretations")
    conn.commit()
    conn.close()


# ---------------- AI SUPPORT QUERIES ----------------

def get_abnormal_labs_by_subject(subject_id: int, limit: int = 5):
    """
    Fetch latest abnormal / critical labs for AI summary.

    LIMIT is mandatory to:
    - prevent long prompts
    - avoid Ollama timeouts
    """

    query = """
    SELECT
        test_name,
        value,
        unit,
        status
    FROM lab_interpretations
    WHERE subject_id = ?
      AND status IN ('ABNORMAL', 'CRITICAL')
    ORDER BY processed_time DESC  -- processed_time must be ISO format
    LIMIT ?
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (subject_id, limit))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "test_name": row["test_name"],
            "value": row["value"],
            "unit": row["unit"],
            "status": row["status"],
        }
        for row in rows
    ]


