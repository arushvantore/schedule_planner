"""Small local account/session store; academic records live in per-user DBs."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from pathlib import Path
import secrets
import sqlite3
import uuid

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
AUTH_DB = DATA / "auth.sqlite"
SESSION_TTL = timedelta(days=14)
COOKIE_NAME = "planner_session"


def _connect():
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        password_salt BLOB NOT NULL,
        password_hash BLOB NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS sessions_user_id ON sessions(user_id);
    """)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _password(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


def create_account(email, password):
    email = email.strip().casefold()
    if len(email) > 254 or email.count("@") != 1 or "." not in email.rsplit("@", 1)[-1]:
        raise ValueError("Enter a valid email address.")
    if len(password) < 12 or len(password) > 256:
        raise ValueError("Use a password between 12 and 256 characters.")
    salt = secrets.token_bytes(16)
    user_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
            (user_id, email, salt, _password(password, salt), now.isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("An account with that email already exists.") from exc
    finally:
        conn.close()
    (DATA / "users").mkdir(parents=True, exist_ok=True)
    return {"id": user_id, "email": email}


def authenticate(email, password):
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().casefold(),)).fetchone()
        if row is None:
            # Keep unknown-email attempts reasonably similar in cost.
            _password(password, b"schedule-planner").hex()
            return None
        if not hmac.compare_digest(_password(password, row["password_salt"]), row["password_hash"]):
            return None
        return {"id": row["id"], "email": row["email"]}
    finally:
        conn.close()


def new_session(user_id):
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + SESSION_TTL
    conn = _connect()
    try:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),))
        conn.execute("INSERT INTO sessions VALUES (?, ?, ?)", (digest, user_id, expires.isoformat()))
        conn.commit()
    finally:
        conn.close()
    return token, expires


def session_user(token):
    if not token:
        return None
    digest = hashlib.sha256(token.encode()).hexdigest()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT u.id, u.email, s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?",
            (digest,),
        ).fetchone()
        if row is None or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
            return None
        return {"id": row["id"], "email": row["email"]}
    finally:
        conn.close()


def revoke_session(token):
    if not token:
        return
    conn = _connect()
    try:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
        conn.commit()
    finally:
        conn.close()


def user_db_path(user_id):
    # user_id comes from the signed-in account record, never a request field.
    if not user_id or any(ch not in "0123456789abcdef" for ch in user_id):
        raise ValueError("Invalid account identifier")
    return DATA / "users" / f"{user_id}.sqlite"
