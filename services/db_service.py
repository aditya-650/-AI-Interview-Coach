"""
services/db_service.py
SQLite database management for Interview IQ:
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

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH = os.path.join(DB_DIR, "interview_iq.db")


class DatabaseService:
    """Manages SQLite database schema, user accounts, and quiz history."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Users table
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

            # Interview sessions / quizzes table
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

    # -------------------------------------------------------------------------
    # PASSWORD HASHING
    # -------------------------------------------------------------------------
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """PBKDF2-HMAC with SHA-256 for secure salted password hashing."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()

    # -------------------------------------------------------------------------
    # USER AUTHENTICATION
    # -------------------------------------------------------------------------
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
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                    (clean_user, clean_email, pw_hash, salt, created_at)
                )
                conn.commit()
                user_id = cursor.lastrowid
                return True, "Registration successful!", {
                    "id": user_id,
                    "username": clean_user,
                    "email": clean_email,
                    "created_at": created_at
                }
        except sqlite3.IntegrityError:
            return False, f"Username '{clean_user}' is already registered. Please log in or choose another.", None
        except Exception as e:
            return False, f"Database error: {str(e)}", None

    def authenticate_user(self, username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticates a user by username or email."""
        identifier = username_or_email.strip()
        if not identifier or not password:
            return False, "Please enter both username and password.", None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (identifier, identifier)
            )
            row = cursor.fetchone()

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

    def get_or_create_oauth_user(self, username: str, email: str) -> Dict[str, Any]:
        """Gets or creates a user account via OAuth / Google Sign-In."""
        clean_user = username.strip()
        clean_email = email.strip().lower()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (clean_email, clean_user))
            row = cursor.fetchone()
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
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
                (clean_user, clean_email, pw_hash, salt, created_at)
            )
            conn.commit()
            return {
                "id": cursor.lastrowid,
                "username": clean_user,
                "email": clean_email,
                "created_at": created_at
            }

    # -------------------------------------------------------------------------
    # USER STATS & QUIZ HISTORY
    # -------------------------------------------------------------------------
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Calculates and returns user interview stats:
        - Total quizzes/interviews completed
        - Average score (percentage)
        - Best score
        """
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
            row = cursor.fetchone()
            return {
                "total_quizzes": row["total_quizzes"] if row else 0,
                "avg_score": round(row["avg_score"], 1) if row else 0.0,
                "best_score": round(row["best_score"], 1) if row else 0.0
            }

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
        """Saves a completed interview session record into SQLite."""
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_json = json.dumps(report_data) if report_data else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO interview_sessions 
                (user_id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, role, difficulty, interview_type, total_questions, overall_score, completed_at, report_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_user_history(self, user_id: int, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns recent completed interview sessions for the user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
            rows = cursor.fetchall()
            history = []
            for r in rows:
                history.append({
                    "id": r["id"],
                    "role": r["role"],
                    "difficulty": r["difficulty"],
                    "interview_type": r["interview_type"],
                    "total_questions": r["total_questions"],
                    "overall_score": r["overall_score"],
                    "completed_at": r["completed_at"],
                    "report": json.loads(r["report_json"]) if r["report_json"] else None
                })
            return history


_db_service_instance: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DatabaseService()
    return _db_service_instance
