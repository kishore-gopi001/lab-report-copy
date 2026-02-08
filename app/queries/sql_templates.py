"""
Pre-defined SQL query templates for common operations.
All queries use parameterized placeholders (?) for safety.
"""

# ============================================================
# COUNT QUERIES
# ============================================================

COUNT_TEMPLATES = {
    # Count all labs for a patient
    "all_labs": {
        "sql": "SELECT COUNT(*) FROM lab_interpretations WHERE subject_id = ?",
        "params": ["subject_id"],
        "description": "Count all laboratory results for a patient"
    },
    
    # Count by status
    "by_status": {
        "sql": "SELECT COUNT(*) FROM lab_interpretations WHERE subject_id = ? AND status = ?",
        "params": ["subject_id", "status"],
        "description": "Count labs by status (NORMAL/ABNORMAL/CRITICAL)"
    },
    
    # Count by test name
    "by_test": {
        "sql": "SELECT COUNT(*) FROM lab_interpretations WHERE subject_id = ? AND test_name = ?",
        "params": ["subject_id", "test_name"],
        "description": "Count specific test results for a patient"
    },
    
    # Count by status and test
    "by_status_and_test": {
        "sql": "SELECT COUNT(*) FROM lab_interpretations WHERE subject_id = ? AND status = ? AND test_name = ?",
        "params": ["subject_id", "status", "test_name"],
        "description": "Count specific test results with status filter"
    },
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_count_query(entities: dict) -> tuple[str, list]:
    """
    Select appropriate count template based on entities.
    Returns: (sql_query, parameters)
    """
    subject_id = entities.get("subject_id")
    status = entities.get("status")
    test_name = entities.get("test_name")
    
    if not subject_id:
        raise ValueError("subject_id is required")
    
    # Select template based on available entities
    if status and test_name:
        template = COUNT_TEMPLATES["by_status_and_test"]
        params = [subject_id, status, test_name]
    elif status:
        template = COUNT_TEMPLATES["by_status"]
        params = [subject_id, status]
    elif test_name:
        template = COUNT_TEMPLATES["by_test"]
        params = [subject_id, test_name]
    else:
        template = COUNT_TEMPLATES["all_labs"]
        params = [subject_id]
    
    return template["sql"], params
