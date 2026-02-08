from database.db import get_connection as get_db
from datetime import datetime, timedelta


# =====================================================
# OVERALL STATUS SUMMARY
# =====================================================

def report_summary():
    """
    Counts labs by status:
    NORMAL / ABNORMAL / CRITICAL / UNKNOWN
    """

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(status, 'UNKNOWN') AS status,
            COUNT(*) AS count
        FROM lab_interpretations
        GROUP BY COALESCE(status, 'UNKNOWN')
    """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return rows


# =====================================================
# PATIENT RISK DISTRIBUTION
# =====================================================

def report_patient_risk_distribution():
    """
    Patient-level risk classification (Optimized SQL version):
    - CRITICAL: level 2
    - ABNORMAL: level 1
    - NORMAL: level 0
    """

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            CASE risk_level
                WHEN 2 THEN 'CRITICAL'
                WHEN 1 THEN 'ABNORMAL'
                ELSE 'NORMAL'
            END AS risk_label,
            COUNT(*) AS count
        FROM (
            SELECT
                subject_id,
                MAX(
                    CASE
                        WHEN status = 'CRITICAL' THEN 2
                        WHEN status = 'ABNORMAL' THEN 1
                        ELSE 0
                    END
                ) AS risk_level
            FROM lab_interpretations
            GROUP BY subject_id
        )
        GROUP BY risk_level
    """)

    rows = cur.fetchall()
    conn.close()

    summary = {
        "NORMAL": 0,
        "ABNORMAL": 0,
        "CRITICAL": 0
    }

    for row in rows:
        summary[row["risk_label"]] = row["count"]

    return summary


# =====================================================
# HIGH-RISK PATIENT COUNT
# =====================================================

def report_high_risk_patients():
    """
    Count of patients with at least one CRITICAL lab
    """

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(DISTINCT subject_id) AS critical_patients
        FROM lab_interpretations
        WHERE status = 'CRITICAL'
    """)

    row = cur.fetchone()
    conn.close()

    return dict(row)


# =====================================================
# LAB IMPACT ANALYSIS
# =====================================================

def report_by_lab():
    """
    Most impacted lab tests (abnormal + critical)
    """

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            test_name,
            status,
            COUNT(DISTINCT subject_id) AS patient_count
        FROM lab_interpretations
        WHERE status IN ('ABNORMAL', 'CRITICAL')
        GROUP BY test_name, status
        ORDER BY patient_count DESC
    """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return rows


# =====================================================
# GENDER RISK SPLIT
# =====================================================

def report_by_gender():
    """
    Abnormal & critical labs grouped by gender
    """

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            gender,
            status,
            COUNT(DISTINCT subject_id) AS patient_count
        FROM lab_interpretations
        WHERE status IN ('ABNORMAL', 'CRITICAL')
        GROUP BY gender, status
    """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return rows


# =====================================================
# UNREVIEWED CRITICAL ALERTS (RAW)
# =====================================================

def unreviewed_critical():
    """
    Raw list of CRITICAL labs not yet reviewed
    """

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM lab_interpretations
        WHERE status = 'CRITICAL'
          AND reviewed = 0
        ORDER BY processed_time DESC
    """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return rows


# =====================================================
# UNREVIEWED CRITICAL SUMMARY (DASHBOARD FRIENDLY)
# =====================================================

def unreviewed_critical_summary():
    """
    Summary of pending critical alerts
    """

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total_unreviewed,
            COUNT(DISTINCT subject_id) AS affected_patients
        FROM lab_interpretations
        WHERE status = 'CRITICAL'
          AND reviewed = 0
    """)

    row = cur.fetchone()
    conn.close()

    return dict(row)


# =====================================================
# RECENT CRITICAL ACTIVITY (LAST 24 HOURS)
# =====================================================

def recent_critical_activity(hours: int = 24):
    """
    Recent CRITICAL labs in the last N hours
    Useful for real-time alert panels
    """

    since_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            test_name,
            COUNT(*) AS count
        FROM lab_interpretations
        WHERE status = 'CRITICAL'
          AND processed_time >= ?
        GROUP BY test_name
        ORDER BY count DESC
    """, (since_time,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return rows
