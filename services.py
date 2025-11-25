# backend/services.py
import hashlib
import datetime
from .db import connect
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def now_ts() -> str:
    return datetime.datetime.utcnow().isoformat()

# ---------------- Admin ----------------
def validate_admin(username: str, password: str) -> bool:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM admins WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return hash_pw(password) == row["password_hash"]

# ---------------- Accounts / Users ----------------
def create_account(account_no: str, name: str, password: str, initial_deposit: float = 0.0):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT account_no FROM accounts WHERE account_no=?", (account_no,))
    if cur.fetchone():
        conn.close()
        raise ValueError("Account number already exists")
    cur.execute(
        "INSERT INTO accounts (account_no, name, password_hash, balance, created_at) VALUES (?, ?, ?, ?, ?)",
        (account_no, name, hash_pw(password), float(initial_deposit), now_ts())
    )
    conn.commit()
    conn.close()
    audit("system", "create_account", account_no)

def authenticate_user(account_no: str, password: str) -> bool:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM accounts WHERE account_no=?", (account_no,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return row["password_hash"] == hash_pw(password)

def get_account(account_no: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts WHERE account_no=?", (account_no,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def list_accounts():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT account_no, name, balance, status, kyc, created_at FROM accounts ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def search_accounts(query: str):
    q = f"%{query.lower()}%"
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT account_no, name, balance FROM accounts WHERE lower(account_no) LIKE ? OR lower(name) LIKE ?", (q, q))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ---------------- Transactions ----------------
def record_tx(tx_type: str, from_acc: str, to_acc: str, amount: float, performed_by: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO transactions (tx_type, from_acc, to_acc, amount, performed_by, timestamp) VALUES (?,?,?,?,?,?)",
                (tx_type, from_acc, to_acc, float(amount), performed_by, now_ts()))
    conn.commit()
    conn.close()
    audit(performed_by, f"tx_{tx_type}", f"{from_acc}->{to_acc}|{amount}")

def deposit(account_no: str, amount: float, performed_by: str):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET balance = balance + ? WHERE account_no=?", (amount, account_no))
    conn.commit()
    conn.close()
    record_tx("deposit", None, account_no, amount, performed_by)

def withdraw(account_no: str, amount: float, performed_by: str):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    acct = get_account(account_no)
    if not acct:
        raise ValueError("Account not found")
    if acct["balance"] < amount:
        raise ValueError("Insufficient funds")
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET balance = balance - ? WHERE account_no=?", (amount, account_no))
    conn.commit()
    conn.close()
    record_tx("withdraw", account_no, None, amount, performed_by)

def transfer(src: str, dst: str, amount: float, performed_by: str):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    src_acct = get_account(src)
    dst_acct = get_account(dst)
    if not src_acct or not dst_acct:
        raise ValueError("Source or destination account not found")
    if src_acct["balance"] < amount:
        raise ValueError("Insufficient funds in source")
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET balance = balance - ? WHERE account_no=?", (amount, src))
    cur.execute("UPDATE accounts SET balance = balance + ? WHERE account_no=?", (amount, dst))
    conn.commit()
    conn.close()
    record_tx("transfer", src, dst, amount, performed_by)

def get_transactions(account_no: str = None, limit: int = 200):
    conn = connect()
    cur = conn.cursor()
    if account_no:
        cur.execute("SELECT * FROM transactions WHERE from_acc=? OR to_acc=? ORDER BY timestamp DESC LIMIT ?", (account_no, account_no, limit))
    else:
        cur.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ---------------- Loans (simple) ----------------
def request_loan(account_no: str, amount: float, term_months: int):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO loans (account_no, amount, term_months, status, created_at) VALUES (?,?,?,?,?)",
                (account_no, amount, term_months, "pending", now_ts()))
    conn.commit()
    conn.close()
    audit("system", "loan_requested", f"{account_no}|{amount}")

def list_loans(status: str = None):
    conn = connect()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM loans WHERE status=? ORDER BY created_at DESC", (status,))
    else:
        cur.execute("SELECT * FROM loans ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_loan_status(loan_id: int, new_status: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE loans SET status=? WHERE id=?", (new_status, loan_id))
    conn.commit()
    conn.close()
    audit("system", "loan_status_change", f"{loan_id}|{new_status}")

# ---------------- Audit / Export ----------------
def audit(actor: str, action: str, details: str = ""):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO audit (actor, action, details, timestamp) VALUES (?,?,?,?)", (actor, action, details, now_ts()))
    conn.commit()
    conn.close()

def list_audit(limit: int = 200):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def export_accounts_csv(path: str = None):
    path = path or str(ROOT / f"accounts_export_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv")
    rows = list_accounts()
    with open(path, "w", newline='', encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["account_no", "name", "balance", "status", "kyc", "created_at"])
        for r in rows:
            w.writerow([r["account_no"], r["name"], r["balance"], r["status"], r.get("kyc", 0), r.get("created_at","")])
    audit("system", "export_accounts_csv", path)
    return path

# optional PDF export (requires reportlab)
