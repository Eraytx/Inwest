from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
from typing import Optional, List
import os
import uvicorn

import database
import engine
import report_generator
import news_service
import config
import scheduler
import search_service
import calendar_service

app = FastAPI(
    title="Inwest API",
    description="Multi-user Backend API for Portfolio Tracker.",
    version="2.0.0"
)

# --- Authentication Middleware ---

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API Token")

    # Expected format: "Bearer <uuid>"
    token = authorization.replace("Bearer ", "").strip()
    user = database.get_user_by_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

# --- Schemas ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SettingsUpdate(BaseModel):
    gemini_api_key: str

class TransactionCreate(BaseModel):
    symbol: str
    asset_class: str
    type: str
    amount: float
    price: float
    timestamp: Optional[str] = None

# --- Lifecycle ---

@app.on_event("startup")
def startup_event():
    try:
        database.init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    app.state.scheduler = scheduler.start_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Routes ---

@app.post("/api/auth/register")
def register(user_data: UserRegister):
    try:
        user = database.create_user(user_data.email, user_data.password)
        return {"status": "success", "token": user["api_token"]}
    except Exception as e:
        if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kullanımda.")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
def login(user_data: UserLogin):
    user = database.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")
    return {"status": "success", "token": user["api_token"]}

# --- Protected Routes (Require Token) ---

@app.get("/api/dashboard")
def get_dashboard_summary(user=Depends(get_current_user)):
    user_id = user["id"]
    try:
        metrics = engine.calculate_portfolio(user_id) # Engine updated to accept user_id
    except Exception as e:
        metrics = {
            "date": "",
            "usd_try_rate": engine.get_usd_try_rate(),
            "total_cost_try": 0.0,
            "total_value_try": 0.0,
            "total_profit_try": 0.0,
            "total_profit_percent": 0.0,
            "daily_change_percent": 0.0,
            "assets": []
        }
        
    history = database.get_portfolio_history(user_id, limit=30)
    reports = database.get_latest_reports(user_id, limit=5)
    news = news_service.fetch_portfolio_news(metrics.get("assets", []))
    
    return {
        "metrics": metrics,
        "history": history,
        "reports": reports,
        "news": news
    }

@app.post("/api/transactions")
def create_transaction(tx: TransactionCreate, user=Depends(get_current_user)):
    try:
        database.add_transaction(
            user_id=user["id"],
            symbol=tx.symbol,
            asset_class=tx.asset_class,
            tx_type=tx.type,
            amount=tx.amount,
            price=tx.price,
            timestamp=tx.timestamp
        )
        return {"status": "success", "message": "Transaction logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/transactions")
def get_transaction_history(limit: int = 100, user=Depends(get_current_user)):
    return database.get_transactions(user["id"], limit=limit)

@app.delete("/api/transactions/{id}")
def delete_transaction(id: int, user=Depends(get_current_user)):
    try:
        database.delete_transaction(user["id"], id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Common Services (Global) ---

@app.get("/api/search")
def autocomplete_search(q: str, type: Optional[str] = None):
    return search_service.search_symbols(q, type)

@app.get("/api/calendar")
def get_macro_calendar():
    return calendar_service.get_economic_calendar()

# --- Settings ---

@app.get("/api/settings")
def get_settings():
    key = os.getenv("GEMINI_API_KEY") or ""
    return {"gemini_api_key": key[:5] + "..." if key else "", "has_key": bool(key)}

@app.post("/api/settings")
def save_settings(settings: SettingsUpdate, user=Depends(get_current_user)):
    # Note: Currently updating global .env (common for all users)
    # In a real app, API Keys should be stored per user in the database.
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
