import sqlite3
import psycopg2
import json
from psycopg2.extras import RealDictCursor
from datetime import datetime
from config import DATABASE_PATH, DATABASE_URL

def get_connection():
    """Returns a connection to the database (PostgreSQL if URL is provided, else SQLite)."""
    if DATABASE_URL:
        # PostgreSQL Connection (Production - Supabase)
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        # SQLite Connection (Local Development)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    """Returns a cursor that yields dict-like rows for both PostgreSQL and SQLite."""
    if DATABASE_URL:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def init_db():
    """Initializes database tables if they do not exist."""
    conn = get_connection()
    cursor = get_cursor(conn)

    # Use different syntax for AUTOINCREMENT in PostgreSQL
    auto_inc = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # 1. Assets table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS assets (
        symbol TEXT PRIMARY KEY,
        asset_class TEXT NOT NULL,
        amount REAL NOT NULL DEFAULT 0.0,
        avg_price REAL NOT NULL DEFAULT 0.0
    )
    """)
    
    # 2. Transactions table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS transactions (
        id {auto_inc},
        symbol TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        price REAL NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)
    
    # 3. Portfolio history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_history (
        date TEXT PRIMARY KEY,
        total_value REAL NOT NULL,
        total_cost REAL NOT NULL,
        daily_change_percent REAL NOT NULL
    )
    """)
    
    # 4. Reports table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS reports (
        id {auto_inc},
        report_type TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        report_text TEXT NOT NULL,
        meta_data TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def add_transaction(symbol, asset_class, tx_type, amount, price, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().isoformat()
        
    conn = get_connection()
    cursor = get_cursor(conn)
    
    tx_type = tx_type.upper()
    symbol = symbol.upper().strip()

    # Placeholder difference between SQLite (?) and PostgreSQL (%s)
    ph = "%s" if DATABASE_URL else "?"

    try:
        # Insert transaction
        cursor.execute(
            f"INSERT INTO transactions (symbol, type, amount, price, timestamp) VALUES ({ph}, {ph}, {ph}, {ph}, {ph})",
            (symbol, tx_type, amount, price, timestamp)
        )
        
        # Check current asset status
        cursor.execute(f"SELECT amount, avg_price FROM assets WHERE symbol = {ph}", (symbol,))
        asset = cursor.fetchone()
        
        if tx_type == "BUY":
            if asset:
                current_amount = asset["amount"]
                current_avg = asset["avg_price"]
                new_amount = current_amount + amount
                if new_amount > 0:
                    new_avg = ((current_amount * current_avg) + (amount * price)) / new_amount
                else:
                    new_avg = 0.0
                cursor.execute(
                    f"UPDATE assets SET amount = {ph}, avg_price = {ph} WHERE symbol = {ph}",
                    (new_amount, new_avg, symbol)
                )
            else:
                cursor.execute(
                    f"INSERT INTO assets (symbol, asset_class, amount, avg_price) VALUES ({ph}, {ph}, {ph}, {ph})",
                    (symbol, asset_class, amount, price)
                )
        elif tx_type == "SELL":
            if asset:
                current_amount = asset["amount"]
                new_amount = max(0.0, current_amount - amount)
                if new_amount <= 1e-8:
                    cursor.execute(f"DELETE FROM assets WHERE symbol = {ph}", (symbol,))
                else:
                    cursor.execute(
                        f"UPDATE assets SET amount = {ph} WHERE symbol = {ph}",
                        (new_amount, symbol)
                    )
            else:
                cursor.execute(
                    f"INSERT INTO assets (symbol, asset_class, amount, avg_price) VALUES ({ph}, {ph}, {ph}, {ph})",
                    (symbol, asset_class, -amount, price)
                )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_assets():
    conn = get_connection()
    cursor = get_cursor(conn)
    cursor.execute("SELECT * FROM assets")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_transactions(limit=100):
    conn = get_connection()
    cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM transactions ORDER BY timestamp DESC LIMIT {ph}", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_portfolio_history(date, total_value, total_cost, daily_change_percent):
    conn = get_connection()
    cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"

    if DATABASE_URL:
        # PostgreSQL ON CONFLICT
        sql = """
            INSERT INTO portfolio_history (date, total_value, total_cost, daily_change_percent)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
            total_value = EXCLUDED.total_value,
            total_cost = EXCLUDED.total_cost,
            daily_change_percent = EXCLUDED.daily_change_percent
        """
    else:
        # SQLite REPLACE
        sql = "INSERT OR REPLACE INTO portfolio_history (date, total_value, total_cost, daily_change_percent) VALUES (?, ?, ?, ?)"

    cursor.execute(sql, (date, total_value, total_cost, daily_change_percent))
    conn.commit()
    conn.close()

def get_portfolio_history(limit=30):
    conn = get_connection()
    cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM portfolio_history ORDER BY date DESC LIMIT {ph}", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in reversed(rows)]

def save_report(report_type, report_text, meta_data=None):
    conn = get_connection()
    cursor = get_cursor(conn)
    generated_at = datetime.now().isoformat()
    meta_json = json.dumps(meta_data) if meta_data else None
    ph = "%s" if DATABASE_URL else "?"

    cursor.execute(
        f"INSERT INTO reports (report_type, generated_at, report_text, meta_data) VALUES ({ph}, {ph}, {ph}, {ph})",
        (report_type, generated_at, report_text, meta_json)
    )
    conn.commit()
    conn.close()

def get_latest_reports(limit=5):
    conn = get_connection()
    cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM reports ORDER BY generated_at DESC LIMIT {ph}", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_transaction(tx_id):
    conn = get_connection()
    cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    try:
        cursor.execute(f"DELETE FROM transactions WHERE id = {ph}", (tx_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    recalculate_assets()

def update_transaction(tx_id, symbol, tx_type, amount, price, timestamp=None):
    conn = get_connection()
    cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    try:
        if timestamp:
            cursor.execute(
                f"UPDATE transactions SET symbol = {ph}, type = {ph}, amount = {ph}, price = {ph}, timestamp = {ph} WHERE id = {ph}",
                (symbol.upper().strip(), tx_type.upper(), amount, price, timestamp, tx_id)
            )
        else:
            cursor.execute(
                f"UPDATE transactions SET symbol = {ph}, type = {ph}, amount = {ph}, price = {ph} WHERE id = {ph}",
                (symbol.upper().strip(), tx_type.upper(), amount, price, tx_id)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    recalculate_assets()

def recalculate_assets():
    conn = get_connection()
    cursor = get_cursor(conn)
    ph = "%s" if DATABASE_URL else "?"
    try:
        cursor.execute("DELETE FROM assets")
        cursor.execute("SELECT * FROM transactions ORDER BY timestamp ASC")
        txs = cursor.fetchall()
        for tx in txs:
            symbol = tx["symbol"].upper().strip()
            tx_type = tx["type"].upper()
            amount = tx["amount"]
            price = tx["price"]
            
            if symbol.endswith(".IS"):
                asset_class = "BIST"
            elif "-" in symbol:
                asset_class = "Crypto"
            else:
                asset_class = "US_Stocks"
            
            cursor.execute(f"SELECT amount, avg_price FROM assets WHERE symbol = {ph}", (symbol,))
            asset = cursor.fetchone()
            
            if tx_type == "BUY":
                if asset:
                    current_amount = asset["amount"]
                    current_avg = asset["avg_price"]
                    new_amount = current_amount + amount
                    new_avg = ((current_amount * current_avg) + (amount * price)) / new_amount if new_amount > 0 else 0.0
                    cursor.execute(f"UPDATE assets SET amount = {ph}, avg_price = {ph} WHERE symbol = {ph}", (new_amount, new_avg, symbol))
                else:
                    cursor.execute(f"INSERT INTO assets (symbol, asset_class, amount, avg_price) VALUES ({ph}, {ph}, {ph}, {ph})", (symbol, asset_class, amount, price))
            elif tx_type == "SELL":
                if asset:
                    current_amount = asset["amount"]
                    new_amount = max(0.0, current_amount - amount)
                    if new_amount <= 1e-8:
                        cursor.execute(f"DELETE FROM assets WHERE symbol = {ph}", (symbol,))
                    else:
                        cursor.execute(f"UPDATE assets SET amount = {ph} WHERE symbol = {ph}", (new_amount, symbol))
                else:
                    cursor.execute(f"INSERT INTO assets (symbol, asset_class, amount, avg_price) VALUES ({ph}, {ph}, {ph}, {ph})", (symbol, asset_class, -amount, price))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
