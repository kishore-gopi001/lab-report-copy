import re
from typing import List, Dict, Any

def truncate_patient_history(content: str, metadata: Dict[str, Any], test_name: str = "") -> str:
    """
    Applies aggressive truncation to patient history to fit context windows.
    Used by both LangGraph nodes and FastAPI fast paths.
    """
    if metadata.get("type") != "patient_history_window" or not content:
        return content or "No content available."

    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Defensive check: if there's very little content, return as is
    if len(lines) <= 5:
        return content

    # Standard clinical history format:
    # 1. Header line
    # 2. Statistics/Summary markers
    # 3. Individual test entries (Date | Test | Value | Status)
    
    header = lines[:3]
    records = lines[3:]
    
    # 1. Top 8 most recent records (reduced from 10 for safety)
    recent = records[:8]
    
    # 2. Top 4 records matching the specific test name
    matching = []
    if test_name:
        test_name_lower = test_name.lower()
        for r in records:
            if test_name_lower in r.lower():
                matching.append(r)
                if len(matching) >= 4:
                    break
    
    # 3. Combine and deduplicate
    final_records = list(dict.fromkeys(recent + matching))
    
    # 4. Final safety truncation (max characters to prevent LLM overload)
    result = "\n".join(header + ["(Showing recent/relevant records for conciseness):"] + final_records)
    
    if len(result) > 1500:
        return result[:1500] + "\n... (further records truncated) ..."
    
    return result
