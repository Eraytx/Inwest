from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
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
    title="Portfolio Tracker & AI Reporting Engine API",
    description="Backend API for BIST and Crypto Portfolio Tracker.",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    # Initialize the database
    try:
        database.init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

    # Start the background task scheduler
    app.state.scheduler = scheduler.start_scheduler()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas for request validation
class SettingsUpdate(BaseModel):
    gemini_api_key: str = Field(..., description="Google Gemini API Key")

class TransactionCreate(BaseModel):
    symbol: str = Field(..., description="Ticker symbol, e.g., FROTO.IS or BTC-USD")
    asset_class: str = Field(..., description="'BIST' or 'Crypto'")
    type: str = Field(..., description="'BUY' or 'SELL'")
    amount: float = Field(..., gt=0, description="Amount of asset traded")
    price: float = Field(..., gt=0, description="Price per unit of the asset")
    timestamp: Optional[str] = Field(None, description="ISO format string, defaults to current time")

class AssetResponse(BaseModel):
    symbol: str
    asset_class: str
    amount: float
    avg_price: float

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

@app.get("/api/dashboard")
def get_dashboard_summary():
    """
    Returns the compiled summary of the portfolio:
    - Current valuation metrics
    - List of assets with market values
    - Historical portfolio data
    - Latest reports
    - Curated news headlines
    """
    try:
        metrics = engine.calculate_portfolio()
    except Exception as e:
        # If portfolio calculations fail, return empty structure instead of crashing
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
        
    history = database.get_portfolio_history(limit=30)
    reports = database.get_latest_reports(limit=5)
    news = news_service.fetch_portfolio_news(metrics.get("assets", []))
    
    return {
        "metrics": metrics,
        "history": history,
        "reports": reports,
        "news": news
    }

@app.get("/api/assets", response_model=List[AssetResponse])
def get_all_assets():
    """Returns the current portfolio holdings."""
    return database.get_assets()

@app.post("/api/transactions")
def create_transaction(tx: TransactionCreate):
    """
    Logs a buy/sell transaction and updates the assets table.
    """
    try:
        success = database.add_transaction(
            symbol=tx.symbol,
            asset_class=tx.asset_class,
            tx_type=tx.type,
            amount=tx.amount,
            price=tx.price,
            timestamp=tx.timestamp
        )
        if success:
            return {"status": "success", "message": "Transaction logged successfully"}
        raise HTTPException(status_code=500, detail="Failed to log transaction")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/transactions")
def get_transaction_history(limit: int = 100):
    """Returns the historical transaction logs."""
    return database.get_transactions(limit=limit)

@app.post("/api/reports/generate")
def trigger_report_generation(background_tasks: BackgroundTasks):
    """
    Triggers the generation of an AI daily/weekly report.
    Can be run as a sync request for manual dashboard generation.
    """
    try:
        report_text = report_generator.generate_ai_report("daily")
        return {"status": "success", "report": report_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

@app.get("/api/reports")
def get_historical_reports(limit: int = 20):
    """Returns past generated AI reports."""
    return database.get_latest_reports(limit=limit)

@app.get("/api/search")
def autocomplete_search(q: str, type: Optional[str] = None):
    """Returns autocomplete suggestions from Yahoo Finance search API."""
    return search_service.search_symbols(q, type)

@app.get("/api/calendar")
def get_macro_calendar():
    """Returns macroeconomic calendar events."""
    return calendar_service.get_economic_calendar()

@app.delete("/api/transactions/{id}")
def delete_transaction(id: int):
    """Deletes a transaction and triggers a full holdings recalculation."""
    try:
        database.delete_transaction(id)
        return {"status": "success", "message": "Transaction deleted and portfolio holdings recalculated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{id}")
def update_transaction(id: int, tx: TransactionCreate):
    """Updates a transaction and triggers a full holdings recalculation."""
    try:
        database.update_transaction(
            tx_id=id,
            symbol=tx.symbol,
            tx_type=tx.type,
            amount=tx.amount,
            price=tx.price,
            timestamp=tx.timestamp
        )
        return {"status": "success", "message": "Transaction updated and portfolio holdings recalculated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
def get_settings():
    """Returns the current settings (API keys masked)."""
    key = os.getenv("GEMINI_API_KEY") or ""
    masked_key = ""
    if key:
        if len(key) > 8:
            masked_key = key[:8] + "..." + key[-4:]
        else:
            masked_key = "..."
    return {
        "gemini_api_key": masked_key,
        "has_key": bool(key)
    }

@app.post("/api/settings")
def save_settings(settings: SettingsUpdate):
    """Saves the Gemini API key to the .env file and updates current config."""
    try:
        # Load existing .env lines
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        
        # Update or add GEMINI_API_KEY
        key_found = False
        new_lines = []
        for line in env_lines:
            if line.strip().startswith("GEMINI_API_KEY="):
                new_lines.append(f"GEMINI_API_KEY={settings.gemini_api_key}\n")
                key_found = True
            else:
                new_lines.append(line)
        
        if not key_found:
            new_lines.append(f"GEMINI_API_KEY={settings.gemini_api_key}\n")
            
        with open(".env", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        # Reload env
        load_dotenv(override=True)
        config.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        
        return {"status": "success", "message": "API Key saved successfully and config updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the Single Page App Frontend
@app.get("/")
def serve_index():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to BIST & Crypto Portfolio Tracker. Frontend files are being configured."}

# Mount static folder for CSS, JS and asset files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    print(f"Starting server on http://{config.HOST}:{config.PORT}...")
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
