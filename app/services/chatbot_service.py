from database.repository import get_abnormal_labs_by_subject
from ai.llm_client import generate_ai_summary

# ---------------- CONSTANTS ----------------

DISCLAIMER = (
    "This explanation is for informational purposes only. "
    "It does not provide medical diagnosis or treatment advice."
)

# ---------------- AI SUMMARY (CACHED) ----------------

_AI_SUMMARY_CACHE: dict[int, dict] = {}


def generate_ai_summary_background(subject_id: int):
    """
    Triggers AI summary generation for abnormal lab results.
    Results are cached in memory for subsequent retrieval.
    """
    if subject_id in _AI_SUMMARY_CACHE:
        return

    # Use repository to fetch data directly
    labs = get_abnormal_labs_by_subject(subject_id, limit=5)

    if not labs:
        _AI_SUMMARY_CACHE[subject_id] = {
            "subject_id": subject_id,
            "summary": "No abnormal or critical lab findings were detected.",
            "disclaimer": DISCLAIMER
        }
        return

    summary_text = generate_ai_summary(labs)

    _AI_SUMMARY_CACHE[subject_id] = {
        "subject_id": subject_id,
        "summary": summary_text.strip(),
        "disclaimer": DISCLAIMER
    }


def get_ai_summary_from_cache(subject_id: int):
    """
    Retrieves AI summary from memory cache if available.
    """
    return _AI_SUMMARY_CACHE.get(subject_id)
