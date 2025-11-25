import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "bank_system.db"

def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def initialize():
    # Create DB and tables if not exists
    conn = connect()
    cur = conn.cursor()

    # admins
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        fullname TEXT,
        role TEXT,
        created_at TEXT
    )""")

    # users/accounts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_no TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        balance REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        kyc INTEGER DEFAULT 0,
        created_at TEXT
    )""")

    # transactions: deposit/withdraw/transfer/loan...
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        from_acc TEXT,
        to_acc TEXT,
        amount REAL,
        performed_by TEXT,
        timestamp TEXT
    )""")

    # loans
    cur.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_no TEXT,
        amount REAL,
        term_months INTEGER,
        status TEXT,
        created_at TEXT
    )""")

    # audit log
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT,
        action TEXT,
        details TEXT,
        timestamp TEXT
    )""")

    conn.commit()

    # ensure default admin (charles / charles123) exists
    cur.execute("SELECT username FROM admins WHERE username=?", ("Admin",))
    if not cur.fetchone():
        import hashlib, datetime
        pw = "Admin123"
        pw_hash = hashlib.sha256(pw.encode()).hexdigest()
        cur.execute("INSERT INTO admins (username, password_hash, fullname, role, created_at) VALUES (?,?,?,?,?)",
                    ("Admin", pw_hash, "Admin", "superadmin", datetime.datetime.utcnow().isoformat()))
        conn.commit()

    conn.close()