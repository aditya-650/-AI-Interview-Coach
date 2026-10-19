"""
services/db_service.py
Hybrid Database Management for Interview IQ:
- Azure SQL Database (Online Cloud Database via Azure Portal) as primary
- Local SQLite database as transparent offline fallback
- User accounts (Sign Up, Login with salted PBKDF2-SHA256 password hashing)
- Interview/Quiz history tracking
- Completion statistics (total quizzes given, average score, best score)
"""

import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    import pyodbc
except ImportError:
    pyodbc = None

from dotenv import load_dotenv

load_dotenv()

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH = os.path.join(DB_DIR, "interview_iq.db")


class DatabaseService:
    """Manages database schema, user accounts, and quiz history on Azure SQL or SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.azure_conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING")
        self.is_cloud = False

        # Attempt to test Azure SQL connection
        if self.azure_conn_str and pyodbc:
            try:
                test_conn = pyodbc.connect(self.azure_conn_str, timeout=5)
                test_conn.close()
                self.is_cloud = True
                print("[DatabaseService] Connected to online Azure SQL Database (interviewiq-db) on Azure Portal.")
            except Exception as e:
                print(f"[DatabaseService] Azure SQL connection failed ({e}), falling back to local SQLite.")
                self.is_cloud = False

        self._init_db()

    def _get_connection(self):
        if self.is_cloud:
            return pyodbc.connect(self.azure_conn_str)
        else:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    @staticmethod
    def _row_to_dict(cursor, row) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {col[0]: row[i] for i, col in enumerate(cursor.description)}

    def _init_db(self):
        """Initializes tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if self.is_cloud:
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
                    CREATE TABLE users (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        username NVARCHAR(100) UNIQUE NOT NULL,
                        email NVARCHAR(255) NOT NULL,
                        password_hash NVARCHAR(255) NOT NULL,
                        salt NVARCHAR(100) NOT NULL,
                        created_at NVARCHAR(50) NOT NULL
                    )
                """)
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='interview_sessions' AND xtype='U')
                    CREATE TABLE interview_sessions (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        user_id INT NOT NULL FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE,
                        role NVARCHAR(100) NOT NULL,
                        difficulty NVARCHAR(50) NOT NULL,
                        interview_type NVARCHAR(50) NOT NULL,
                        total_questions INT NOT NULL,
                        overall_score FLOAT NOT NULL,
                        completed_at NVARCHAR(50) NOT NULL,
                        report_json NVARCHAR(MAX)
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interview_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        difficulty TEXT NOT NULL,
                        interview_type TEXT NOT NULL,
                        total_questions INTEGER NOT NULL,
                        overall_score REAL NOT NULL,
                        completed_at TEXT NOT NULL,
                        report_json TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
            conn.commit()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """PBKDF2-HMAC with SHA-256 for secure salted password hashing."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Registers a new user with validation and salted password hashing."""
        clean_user = username.strip()
        clean_email = email.strip()

        if not clean_user or len(clean_user) < 3:
            return False, "Username must be at least 3 characters long.", None

        if not clean_email or "@" not in clean_email:
            return False, "Please provide a valid email address.", None

        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        salt = secrets.token_hex(16)
        pw_hash = self._hash_password(password, salt)
        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.is_cloud:
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, salt, created_at)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?, ?, ?)
                    """, (clean_user, clean_email, pw_hash, salt, created_at))
                    user_id = cursor.fetchone()[0]
                else:
                    cursor.execute(
                        "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                        (clean_user, clean_email, pw_hash, salt, created_at)
                    )
                    user_id = cursor.lastrowid
                conn.commit()
                return True, "Registration successful!", {
                    "id": user_id,
                    "username": clean_user,
                    "email": clean_email,
                    "created_at": created_at
                }
        except Exception as e:
            err_msg = str(e)
            if "UNIQUE" in err_msg.upper() or "DUPLICATE" in err_msg.upper() or "INTEGRITY" in err_msg.upper():
                return False, f"Username '{clean_user}' is already registered. Please log in or choose another.", None
            return False, f"Database error: {err_msg}", None

    def authenticate_user(self, username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticates a user by username or email."""
        identifier = username_or_email.strip()
        if not identifier or not password:
            return False, "Please enter both username and password.", None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE username = ? OR email = ?",
                    (identifier, identifier)
                )
                raw_row = cursor.fetchone()
                row = self._row_to_dict(cursor, raw_row)

                if not row:
                    return False, "User not found. Please check your credentials or sign up.", None

                salt = row["salt"]
                expected_hash = row["password_hash"]
                provided_hash = self._hash_password(password, salt)

                if provided_hash != expected_hash:
                    return False, "Incorrect password. Please try again.", None

                return True, "Login successful!", {
                    "id": row["id"],
                    "username": row["username"],
                    "email": row["email"],
                    "created_at": row["created_at"]
                }
        except Exception as e:
            return False, f"Authentication error. Please try again. ({str(e)[:80]})", None

    def get_or_create_oauth_user(self, username: str, email: str) -> Dict[str, Any]:
        """Gets or creates a user account via OAuth / Google Sign-In."""
        clean_user = username.strip()
        clean_email = email.strip().lower()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (clean_email, clean_user))
                raw_row = cursor.fetchone()
                row = self._row_to_dict(cursor, raw_row)
                if row:
                    return {
                        "id": row["id"],
                        "username": row["username"],
                        "email": row["email"],
                        "created_at": row["created_at"]
                    }

                # Create user if doesn't exist
                salt = secrets.token_hex(16)
                pw_hash = self._hash_password(secrets.token_hex(24), salt)
                created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                if self.is_cloud:
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, salt, created_at)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?, ?, ?)
                    """, (clean_user, clean_email, pw_hash, salt, created_at))
                    user_id = cursor.fetchone()[0]
                else:
                    cursor.execute(
                        "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                        (clean_user, clean_email, pw_hash, salt, created_at)
                    )
                    user_id = cursor.lastrowid

                conn.commit()
                return {
                    "id": user_id,
                    "username": clean_user,
                    "email": clean_email,
                    "created_at": created_at
                }
        except Exception as e:
            print(f"[DatabaseService] get_or_create_oauth_user error: {e}")
            # Return a temporary in-memory user so OAuth login doesn't crash the app
            return {
                "id": 0,
                "username": clean_user,
                "email": clean_email,
                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Calculates and returns user interview stats."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_quizzes,
                        COALESCE(AVG(overall_score), 0) as avg_score,
                        COALESCE(MAX(overall_score), 0) as best_score
                    FROM interview_sessions
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )
                raw_row = cursor.fetchone()
                row = self._row_to_dict(cursor, raw_row)
                return {
                    "total_quizzes": int(row["total_quizzes"]) if row else 0,
                    "avg_score": round(float(row["avg_score"]), 1) if row else 0.0,
                    "best_score": round(float(row["best_score"]), 1) if row else 0.0
                }
        except Exception as e:
            print(f"[DatabaseService] get_user_stats error: {e}")
            return {"total_quizzes": 0, "avg_score": 0.0, "best_score": 0.0}

    def save_interview_session(
        self,
        user_id: int,
        role: str,
        difficulty: str,
        interview_type: str,
        total_questions: int,
        overall_score: float,
        report_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Saves a completed interview session record into Azure SQL or SQLite."""
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_json = json.dumps(report_data) if report_data else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if self.is_cloud:
                cursor.execute(
                    """
                    INSERT INTO interview_sessions 
                    (user_id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json)
                )
                session_id = cursor.fetchone()[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO interview_sessions 
                    (user_id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json)
                )
                session_id = cursor.lastrowid
            conn.commit()
            return session_id

    def get_user_history(self, user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns recent completed interview sessions for the user."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.is_cloud:
                    cursor.execute(
                        """
                        SELECT TOP (?) id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json
                        FROM interview_sessions
                        WHERE user_id = ?
                        ORDER BY id DESC
                        """,
                        (limit, user_id)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json
                        FROM interview_sessions
                        WHERE user_id = ?
                        ORDER BY id DESC
                        LIMIT ?
                        """,
                        (user_id, limit)
                    )
                raw_rows = cursor.fetchall()
                history = []
                for r in raw_rows:
                    row = self._row_to_dict(cursor, r)
                    history.append({
                        "id": row["id"],
                        "role": row["role"],
                        "difficulty": row["difficulty"],
                        "interview_type": row["interview_type"],
                        "total_questions": row["total_questions"],
                        "overall_score": float(row["overall_score"]),
                        "completed_at": row["completed_at"],
                        "report": json.loads(row["report_json"]) if row["report_json"] else None
                    })
                return history
        except Exception as e:
            print(f"[DatabaseService] get_user_history error: {e}")
            return []


_db_service_instance: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DatabaseService()
    return _db_service_instance
