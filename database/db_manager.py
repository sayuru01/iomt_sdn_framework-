# database/db_manager.py
import sqlite3
import threading
import os

# Always resolve path relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "iomt_security.db")

# One lock for all write operations
_lock = threading.Lock()

def get_connection():
    """Create and return a configured SQLite connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")    # prevent lock errors
    conn.execute("PRAGMA synchronous=NORMAL;")  # performance balance
    conn.row_factory = sqlite3.Row              # column name access
    return conn

def safe_write(query, params=()):
    """
    Thread-safe write — returns inserted row ID.
    Used by ALL modules writing to DB.
    """
    with _lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"[DB ERROR] Write failed: {e}")
            raise e
        finally:
            conn.close()

def safe_read(query, params=(), fetch_one=False):
    """
    Read operation — returns dict or list of dicts.
    Flask/SocketIO JSON serialization compatible.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch_one:
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[DB ERROR] Read failed: {e}")
        raise e
    finally:
        conn.close()

def safe_execute_many(query, params_list):
    """
    Bulk write — for inserting multiple rows at once.
    Used by baseline experiment (many readings at once).
    """
    with _lock:
        conn = get_connection()
        try:
            conn.executemany(query, params_list)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[DB ERROR] Bulk write failed: {e}")
            raise e
        finally:
            conn.close()

# Quick test
if __name__ == "__main__":
    print(f"[DB] Path: {DB_PATH}")
    print("[DB] db_manager.py loaded OK ")