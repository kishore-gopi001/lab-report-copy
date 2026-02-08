# ==============================================================================
# LAB REPORT INTERPRETATION SYSTEM - CORE API
# ==============================================================================
# This FastAPI application serves as the backend for the Lab Report dashboard
# and the agentic chatbot. It integrates LangGraph for complex medical queries
# and Random Forest models for risk prediction.
# ==============================================================================

import json
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import create_access_token, get_current_user, verify_password, get_password_hash

# --- Internal Service Imports ---
from app.services.chatbot_service import (
    generate_ai_summary_background,
    get_ai_summary_from_cache,
)
from app.services.report_service import (
    report_summary,
    report_by_lab,
    report_by_gender,
    unreviewed_critical,
    report_patient_risk_distribution,
    report_high_risk_patients,
    unreviewed_critical_summary,
    recent_critical_activity,
)
from app.services.risk_service import (
    get_patient_risk_score,
    get_high_risk_patients,
    get_risk_distribution,
)
from database.db import get_connection

# AI imports are now mostly in services and chat_handler

# --- App Initialization ---
app = FastAPI(
    title="Lab Report Interpretation System",
    description="Human-like chatbot with AI-assisted lab summaries (Non-diagnostic)",
    version="1.2.1",
)

# --- Static Files & Template Configuration ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# =====================================================
# DASHBOARD ROUTES
# =====================================================
# --- Root Endpoint (Base URL) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Redirects to login page or dashboard.
    """
    return templates.TemplateResponse("login.html", {"request": request})

# --- Authentication Endpoints ---
@app.post("/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"DEBUG: Login attempt for user: '{form_data.username}' (len: {len(form_data.username)})")
    print(f"DEBUG: Password length received: {len(form_data.password)}")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (form_data.username.strip(),))
    user = cur.fetchone()
    conn.close()
    
    if not user:
        print(f"DEBUG: User '{form_data.username}' not found in DB")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    is_valid = verify_password(form_data.password, user["hashed_password"])
    
    # --- EMERGENCY FALLBACK (ONLY for initial setup verification) ---
    if not is_valid and form_data.username == "admin" and form_data.password == "admin123":
        print("DEBUG: Using Emergency Fallback Login for admin")
        is_valid = True
    
    if not is_valid:
        print(f"DEBUG: Password verification failed for '{form_data.username}'")
        # Let's see if stripping helps (though password shouldn't be stripped usually)
        is_valid_stripped = verify_password(form_data.password.strip(), user["hashed_password"])
        print(f"DEBUG: Stripped Password match: {is_valid_stripped}")
        
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/check-header")
async def check_header(request: Request):
    auth_header = request.headers.get("Authorization")
    print(f"SUPER_DEBUG: Authorization Header: {auth_header}")
    return {"header": auth_header}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """General lab reports and statistics dashboard"""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


@app.get("/ml-dashboard", response_class=HTMLResponse)
async def ml_dashboard(request: Request):
    """ML-powered patient risk prediction dashboard"""
    return templates.TemplateResponse(
        "ml-dashboard.html",
        {"request": request}
    )



# =====================================================
# AI SUMMARY API (BACKGROUND + POLLING)
# =====================================================

@app.get("/chat/patient/{subject_id}/ai-summary")
async def patient_ai_summary(subject_id: int, background_tasks: BackgroundTasks, current_user: Any = Depends(get_current_user)):
    """
    Returns AI summary if ready.
    Otherwise triggers background generation.
    """

    cached = get_ai_summary_from_cache(subject_id)

    if cached:
        return cached

    background_tasks.add_task(
        generate_ai_summary_background,
        subject_id
    )

    return {
        "message": (
            "Generating AI summary. "
            "This may take a few seconds. Please refresh shortly."
        )
    }


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")




# ==============================================================================
# REPORTING APIs (DASHBOARD INSIGHTS)
# ==============================================================================

@app.get("/reports/summary")
async def reports_summary(current_user: Any = Depends(get_current_user)):
    """Returns a categorical count of all lab results (NORMAL, ABNORMAL, etc.)."""
    return report_summary()


@app.get("/reports/patient-risk-distribution")
async def reports_patient_risk_dist(current_user: Any = Depends(get_current_user)):
    return report_patient_risk_distribution()


@app.get("/reports/high-risk-patients")
async def reports_high_risk(current_user: Any = Depends(get_current_user)):
    return report_high_risk_patients()


@app.get("/reports/by-lab")
async def reports_by_lab(current_user: Any = Depends(get_current_user)):
    return report_by_lab()


@app.get("/reports/by-gender")
async def reports_by_gender(current_user: Any = Depends(get_current_user)):
    return report_by_gender()


@app.get("/reports/unreviewed-critical")
async def reports_unreviewed_critical(current_user: Any = Depends(get_current_user)):
    return unreviewed_critical()


@app.get("/reports/unreviewed-critical-summary")
async def reports_unreviewed_summary(current_user: Any = Depends(get_current_user)):
    return unreviewed_critical_summary()


@app.get("/reports/recent-critical")
async def reports_recent_critical(current_user: Any = Depends(get_current_user)):
    return recent_critical_activity()


# =====================================================
# RISK PREDICTION APIs (ML MODEL)
# =====================================================

@app.get("/predict/patient/{subject_id}/risk")
async def predict_patient_risk_score(subject_id: int, current_user: Any = Depends(get_current_user)):
    """
    Predict risk score for a specific patient using trained ML model
    Returns: risk_level (0-2), risk_label, confidence, probabilities
    """
    return get_patient_risk_score(subject_id)


@app.get("/predict/risk-distribution")
async def predict_risk_distribution(current_user: Any = Depends(get_current_user)):
    """
    Get distribution of patients across risk levels
    """
    return get_risk_distribution()


@app.get("/predict/high-risk")
async def predict_high_risk_patients(risk_level: int = 2, limit: int = 50, current_user: Any = Depends(get_current_user)):
    """
    Get patients with high risk scores
    risk_level: 1 = ABNORMAL or higher, 2 = CRITICAL only
    """
    return get_high_risk_patients(risk_level, limit)




# ==============================================================================
# AGENTIC CHATBOT API (LANGGRAPH + STREAMING)
# ==============================================================================

@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest, current_user: Any = Depends(get_current_user)):
    """
    OPTIMIZED Streaming LangGraph Agent with Fast-Path:
    Delegates to handle_chat_stream service.
    """
    from app.services.chat_handler import handle_chat_stream
    return StreamingResponse(handle_chat_stream(payload.question.strip()), media_type="text/event-stream")

