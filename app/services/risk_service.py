"""
Risk Scoring Service
Provides APIs for risk prediction and patient risk reports
"""

from database.db import get_connection as get_db
from ai.risk_model import predict_patient_risk


def get_patient_risk_score(subject_id: int):
    """
    Get risk prediction for a specific patient
    """
    return predict_patient_risk(subject_id)




def get_high_risk_patients(risk_level: int = 2, limit: int = 50):
    """
    Get all patients above a certain risk level
    risk_level: 1 = ABNORMAL, 2 = CRITICAL
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT subject_id
        FROM lab_interpretations
        WHERE subject_id IN (
            SELECT subject_id
            FROM lab_interpretations
            WHERE status IN ('ABNORMAL', 'CRITICAL')
        )
        LIMIT ?
    """, (limit,))

    patients = cur.fetchall()
    conn.close()

    high_risk = []
    for patient in patients:
        score = predict_patient_risk(patient['subject_id'])
        if 'risk_level' in score and score['risk_level'] >= risk_level:
            high_risk.append(score)

    return sorted(high_risk, key=lambda x: x.get('confidence', 0), reverse=True)


def get_risk_distribution():
    """
    Get distribution of patients across risk levels
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT subject_id
        FROM lab_interpretations
    """)

    patients = cur.fetchall()
    conn.close()

    distribution = {
        'NORMAL': [],
        'ABNORMAL': [],
        'CRITICAL': []
    }

    for patient in patients:
        score = predict_patient_risk(patient['subject_id'])
        if 'risk_label' in score:
            distribution[score['risk_label']].append(score)

    # Return counts
    return {
        'NORMAL': len(distribution['NORMAL']),
        'ABNORMAL': len(distribution['ABNORMAL']),
        'CRITICAL': len(distribution['CRITICAL']),
        'total': len(patients)
    }
