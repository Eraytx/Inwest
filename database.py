import sqlite3
import psycopg2
import json
import hashlib
import uuid
from psycopg2.extras import RealDictCursor
from datetime import datetime
from config import DATABASE_PATH, DATABASE_URL

def get_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    if DATABASE_URL:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def init_db():
    """Drops old tables and initializes the database with the new multi-user schema."""
    conn = get_connection()
    cursor = get_cursor(conn)
    auto_inc = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Check if we need to migration (Detect old schema)
    needs_reset = False
    try:
        cursor.execute("SELECT user_id FROM transactions LIMIT 1")
    except Exception:
        needs_reset = True
        if DATABASE_URL: conn.rollback()
        print("Old schema detected. Resetting tables for multi-user support...")

    if needs_reset:
        # Nuclear option: Drop existing tables to ensure PK constraints are set correctly
        tables = ["reports", "portfolio_history", "transactions", "assets", "users"]
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            except Exception:
                if DATABASE_URL: conn.rollback()

    # 1. Users table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {auto_inc},
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        api_token TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # 2. Assets table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS assets (
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        asset_class TEXT NOT NULL,
        amount REAL NOT NULL DEFAULT 0.0,
        avg_price REAL NOT NULL DEFAULT 0.0,
        PRIMARY KEY (user_id, symbol)
    )
    """)

    # 3. Transactions table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS transactions (
        id {auto_inc},
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        price REAL NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    # 4. Portfolio history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_history (
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        total_value REAL NOT NULL,
        total_cost REAL NOT NULL,
        daily_change_percent REAL NOT NULL,
        PRIMARY KEY (user_id, date)
    )
    """)

    # 5. Reports table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS reports (
        id {auto_inc},
        user_id INTEGER NOT NULL,
        report_type TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        report_text TEXT NOT NULL,
        meta_data TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("Database schema is up to date.")

# --- Auth Functions ---

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password):
    conn = get_connection()
    cursor = get_cursor(conn)
    password_hash = hash_password(password)
    api_token = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    ph = "%s" if DATABASE_URL else "?"
    try:
        cursor.execute(f"INSERT INTO users (email, password_hash, api_token, created_at) VALUES ({ph}, {ph}, {ph}, {ph}) RETURNING id", (email.lower(), password_hash, api_token, created_at))
        user_id = cursor.fetchone()['id'] if DATABASE_URL else cursor.lastrowid
        conn.commit()
        return {"id": user_id, "api_token": api_token}
    except Exception as e:
        conn.rollback(); raise e
    finally: conn.close()

def authenticate_user(email, password):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT id, email, api_token FROM users WHERE email = {ph} AND password_hash = {ph}", (email.lower(), hash_password(password)))
    user = cursor.fetchone(); conn.close()
    return dict(user) if user else None

def get_user_by_token(token):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT id, email FROM users WHERE api_token = {ph}", (token,))
    user = cursor.fetchone(); conn.close()
    return dict(user) if user else None

# --- Data Functions ---

def add_transaction(user_id, symbol, asset_class, tx_type, amount, price, timestamp=None):
    if timestamp is None: timestamp = datetime.now().isoformat()
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    try:
        cursor.execute(f"INSERT INTO transactions (user_id, symbol, type, amount, price, timestamp) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})", (user_id, symbol.upper(), tx_type.upper(), amount, price, timestamp))
        cursor.execute(f"SELECT amount, avg_price FROM assets WHERE user_id = {ph} AND symbol = {ph}", (user_id, symbol.upper()))
        asset = cursor.fetchone()
        if tx_type.upper() == "BUY":
            if asset:
                new_amount = asset["amount"] + amount
                new_avg = ((asset["amount"] * asset["avg_price"]) + (amount * price)) / new_amount if new_amount > 0 else 0.0
                cursor.execute(f"UPDATE assets SET amount = {ph}, avg_price = {ph} WHERE user_id = {ph} AND symbol = {ph}", (new_amount, new_avg, user_id, symbol.upper()))
            else:
                cursor.execute(f"INSERT INTO assets (user_id, symbol, asset_class, amount, avg_price) VALUES ({ph}, {ph}, {ph}, {ph}, {ph})", (user_id, symbol.upper(), asset_class, amount, price))
        elif tx_type.upper() == "SELL":
            if asset:
                new_amount = max(0.0, asset["amount"] - amount)
                if new_amount <= 1e-8: cursor.execute(f"DELETE FROM assets WHERE user_id = {ph} AND symbol = {ph}", (user_id, symbol.upper()))
                else: cursor.execute(f"UPDATE assets SET amount = {ph} WHERE user_id = {ph} AND symbol = {ph}", (new_amount, user_id, symbol.upper()))
        conn.commit()
        return True
    except Exception as e: conn.rollback(); raise e
    finally: conn.close()

def get_assets(user_id):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM assets WHERE user_id = {ph}", (user_id,))
    rows = cursor.fetchall(); conn.close()
    return [dict(row) for row in rows]

def get_transactions(user_id, limit=100):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM transactions WHERE user_id = {ph} ORDER BY timestamp DESC LIMIT {ph}", (user_id, limit))
    rows = cursor.fetchall(); conn.close()
    return [dict(row) for row in rows]

def save_portfolio_history(user_id, date, total_value, total_cost, daily_change_percent):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    if DATABASE_URL:
        sql = "INSERT INTO portfolio_history (user_id, date, total_value, total_cost, daily_change_percent) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (user_id, date) DO UPDATE SET total_value=EXCLUDED.total_value, total_cost=EXCLUDED.total_cost, daily_change_percent=EXCLUDED.daily_change_percent"
    else:
        sql = "INSERT OR REPLACE INTO portfolio_history (user_id, date, total_value, total_cost, daily_change_percent) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(sql, (user_id, date, total_value, total_cost, daily_change_percent))
    conn.commit(); conn.close()

def get_portfolio_history(user_id, limit=30):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM portfolio_history WHERE user_id = {ph} ORDER BY date DESC LIMIT {ph}", (user_id, limit))
    rows = cursor.fetchall(); conn.close()
    return [dict(row) for row in reversed(rows)]

def save_report(user_id, report_type, report_text, meta_data=None):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"INSERT INTO reports (user_id, report_type, generated_at, report_text, meta_data) VALUES ({ph}, {ph}, {ph}, {ph}, {ph})", (user_id, report_type, datetime.now().isoformat(), report_text, json.dumps(meta_data) if meta_data else None))
    conn.commit(); conn.close()

def get_latest_reports(user_id, limit=5):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM reports WHERE user_id = {ph} ORDER BY generated_at DESC LIMIT {ph}", (user_id, limit))
    rows = cursor.fetchall(); conn.close()
    return [dict(row) for row in rows]

def delete_transaction(user_id, tx_id):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    try:
        cursor.execute(f"DELETE FROM transactions WHERE user_id = {ph} AND id = {ph}", (user_id, tx_id))
        conn.commit()
    except Exception as e: conn.rollback(); raise e
    finally: conn.close()
    recalculate_assets(user_id)

def recalculate_assets(user_id):
    conn = get_connection(); cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    try:
        cursor.execute(f"DELETE FROM assets WHERE user_id = {ph}", (user_id,))
        cursor.execute(f"SELECT * FROM transactions WHERE user_id = {ph} ORDER BY timestamp ASC", (user_id,))
        txs = cursor.fetchall()
        for tx in txs:
            symbol = tx["symbol"].upper()
            if symbol.endswith(".IS"): ac = "BIST"
            elif "-" in symbol: ac = "Crypto"
            else: ac = "US_Stocks"
            add_transaction(user_id, symbol, ac, tx["type"], tx["amount"], tx["price"], tx["timestamp"])
        conn.commit()
    except Exception as e: conn.rollback(); raise e
    finally: conn.close()
