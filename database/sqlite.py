"""SQLite Database Implementation

A lightweight, file-based database alternative to MySQL.
Compatible with the Database interface.
"""
import logging
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from database.base import Database

logger = logging.getLogger(__name__)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SQLiteDatabase(Database):
    """SQLite Database Management Class"""

    def __init__(self, db_path="bot.db"):
        """Initialize database connection"""
        self.db_path = os.getenv('SQLITE_PATH', db_path)
        logger.info(f"SQLite Database Initialization: {self.db_path}")
        self.init_database()

    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = dict_factory
        return conn

    def init_database(self):
        """Initialize database table structure"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Users Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    balance INTEGER DEFAULT 1,
                    is_blocked INTEGER DEFAULT 0,
                    invited_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checkin TIMESTAMP NULL
                )
                """
            )
            # Indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invited_by ON users(invited_by)")

            # Invitations Records Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS invitations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter_id INTEGER NOT NULL,
                    invitee_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inviter_id) REFERENCES users(user_id),
                    FOREIGN KEY (invitee_id) REFERENCES users(user_id)
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inviter ON invitations(inviter_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invitee ON invitations(invitee_id)")

            # Verification Records Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    verification_type TEXT NOT NULL,
                    verification_url TEXT,
                    verification_id TEXT,
                    status TEXT NOT NULL,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ver_user_id ON verifications(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ver_type ON verifications(verification_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ver_created ON verifications(created_at)")

            # Card Keys Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS card_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_code TEXT UNIQUE NOT NULL,
                    balance INTEGER NOT NULL,
                    max_uses INTEGER DEFAULT 1,
                    current_uses INTEGER DEFAULT 0,
                    expire_at TIMESTAMP NULL,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_key_code ON card_keys(key_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_by ON card_keys(created_by)")

            # Card Key Usage Records
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS card_key_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_code TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_key_code ON card_key_usage(key_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_id ON card_key_usage(user_id)")

            # Transaction Ledger Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transaction_at TIMESTAMP NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_created ON ledger(created_at)")

            # Settings Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.commit()
            logger.info("SQLite database tables initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                # Convert timestamps to ISO strings for compatibility
                if row.get('created_at'):
                    if isinstance(row['created_at'], str):
                         # Already string
                         pass
                    elif hasattr(row['created_at'], 'isoformat'):
                        row['created_at'] = row['created_at'].isoformat()
                if row.get('last_checkin'):
                    if isinstance(row['last_checkin'], str):
                        pass
                    elif hasattr(row['last_checkin'], 'isoformat'):
                        row['last_checkin'] = row['last_checkin'].isoformat()
                return row
            return None
        finally:
            cursor.close()
            conn.close()

    def user_exists(self, user_id: int) -> bool:
        return self.get_user(user_id) is not None

    def create_user(
        self, user_id: int, username: str, full_name: str, invited_by: Optional[int] = None
    ) -> bool:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (user_id, username, full_name, invited_by, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, username, full_name, invited_by),
            )

            if invited_by:
                # Add reward to inviter
                cursor.execute(
                    "UPDATE users SET balance = balance + 2 WHERE user_id = ?",
                    (invited_by,),
                )
                cursor.execute(
                    """
                    INSERT INTO invitations (inviter_id, invitee_id, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (invited_by, user_id),
                )

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_all_user_ids(self) -> List[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM users")
            rows = cursor.fetchall()
            return [row['user_id'] for row in rows]
        finally:
            cursor.close()
            conn.close()

    # Balance Management
    def get_balance(self, user_id: int) -> int:
        user = self.get_user(user_id)
        return user['balance'] if user else 0

    def add_balance(self, user_id: int, amount: int, description: str = "", metadata: Optional[Dict] = None, transaction_at: Optional[datetime] = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (amount, user_id),
            )
            self.log_transaction(user_id, amount, 'topup' if amount > 5 else 'reward', description, metadata, transaction_at)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add balance: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def deduct_balance(self, user_id: int, amount: int, description: str = "", metadata: Optional[Dict] = None, transaction_at: Optional[datetime] = None) -> bool:
        user = self.get_user(user_id)
        if not user or user["balance"] < amount:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (amount, user_id),
            )
            self.log_transaction(user_id, -amount, 'spend', description, metadata, transaction_at)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to deduct balance: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def log_transaction(self, user_id: int, amount: int, transaction_type: str, description: str = "", metadata: Optional[Dict] = None, transaction_at: Optional[datetime] = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            # If transaction_at is None, use current time
            if transaction_at is None:
                cursor.execute(
                    """
                    INSERT INTO ledger (user_id, amount, type, description, metadata, created_at, transaction_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (user_id, amount, transaction_type, description, metadata_json)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO ledger (user_id, amount, type, description, metadata, created_at, transaction_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    """,
                    (user_id, amount, transaction_type, description, metadata_json, transaction_at)
                )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}")
            return False  # Usually called within another transaction, so don't rollback/close here if sharing conn
        finally:
            cursor.close()
            conn.close()

    # Blacklist Management
    def is_user_blocked(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user and user["is_blocked"] == 1

    def block_user(self, user_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    def unblock_user(self, user_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    def get_blacklist(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE is_blocked = 1")
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    # Check-in Management
    def can_checkin(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        
        last_checkin = user.get("last_checkin")
        if not last_checkin:
            return True

        if isinstance(last_checkin, str):
            try:
                last_date = datetime.fromisoformat(last_checkin).date()
            except ValueError:
                 # Fallback if format is weird
                 return True
        elif hasattr(last_checkin, 'date'):
             last_date = last_checkin.date()
        else:
            return True # Should not happen

        today = datetime.now().date()
        return last_date < today

    def checkin(self, user_id: int) -> bool:
        if not self.can_checkin(user_id):
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE users
                SET balance = balance + 1, last_checkin = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Checkin failed: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    # Card Key Management
    def create_card_key(
        self, key_code: str, balance: int, created_by: int, 
        max_uses: int = 1, expire_days: Optional[int] = None
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            expire_at = None
            if expire_days:
                expire_at = datetime.now() + timedelta(days=expire_days)

            cursor.execute(
                """
                INSERT INTO card_keys (key_code, balance, max_uses, created_by, created_at, expire_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """,
                (key_code, balance, max_uses, created_by, expire_at),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_card_key_info(self, key_code: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM card_keys WHERE key_code = ?", (key_code,))
            row = cursor.fetchone()
            # Convert timestamp strings to datetime objects if needed matching MySQL behavior?
            # Actually PyMySQL returns datetime, sqlite returns string (usually).
            # The base class hints at returning Dict, typically callers handle it.
            # But specific date logic might exist outside.
            return row
        finally:
            cursor.close()
            conn.close()

    def use_card_key(self, key_code: str, user_id: int) -> Optional[int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM card_keys WHERE key_code = ?", (key_code,))
            card = cursor.fetchone()
            if not card:
                return None
            
            # Check expiry (Parse string to datetime if needed)
            if card['expire_at']:
                expire_at = card['expire_at']
                if isinstance(expire_at, str):
                    try:
                        expire_at = datetime.fromisoformat(expire_at)
                    except:
                        pass # Ignore parsing error?
                
                if isinstance(expire_at, datetime) and datetime.now() > expire_at:
                    return -2

            if card["current_uses"] >= card["max_uses"]:
                return -1
            
            # Check usage
            cursor.execute(
                "SELECT COUNT(*) as count FROM card_key_usage WHERE key_code = ? AND user_id = ?",
                (key_code, user_id),
            )
            if cursor.fetchone()['count'] > 0:
                return -3
            
            # Update usage
            cursor.execute(
                "UPDATE card_keys SET current_uses = current_uses + 1 WHERE key_code = ?",
                (key_code,)
            )
            
            # Record usage
            cursor.execute(
                "INSERT INTO card_key_usage (key_code, user_id, used_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key_code, user_id)
            )
            
            # Add balance
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (card['balance'], user_id)
            )
            
            conn.commit()
            return card['balance']
            
        except Exception as e:
            logger.error(f"Failed to use card key: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    def get_all_card_keys(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM card_keys ORDER BY created_at DESC")
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    # Verification Management
    def add_verification(
        self, user_id: int, verification_type: str, verification_url: str,
        status: str, result: str = "", verification_id: Optional[str] = ""
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO verifications
                (user_id, verification_type, verification_url, verification_id, status, result, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, verification_type, verification_url, verification_id, status, result),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add verification: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_user_verifications(self, user_id: int, limit: int = 10) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT * FROM verifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT * FROM ledger
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            results = list(cursor.fetchall())
            # Convert ISO strings
            for row in results:
                if row.get('created_at') and hasattr(row['created_at'], 'isoformat'):
                    row['created_at'] = row['created_at'].isoformat()
                if row.get('transaction_at') and hasattr(row['transaction_at'], 'isoformat'):
                    row['transaction_at'] = row['transaction_at'].isoformat()
            return results
        finally:
            cursor.close()
            conn.close()

    def get_user_stats(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            stats = {}
            cursor.execute("SELECT COUNT(*) as total FROM users")
            stats['total_users'] = cursor.fetchone()['total']

            cursor.execute("SELECT SUM(balance) as total_gems FROM users")
            row = cursor.fetchone()
            stats['total_gems'] = row['total_gems'] if row and row['total_gems'] else 0

            cursor.execute("SELECT COUNT(*) as blocked FROM users WHERE is_blocked = 1")
            stats['blocked_users'] = cursor.fetchone()['blocked']
            
            # Active users (last 7 days) - SQLite syntax
            cursor.execute("""
                SELECT COUNT(*) as active 
                FROM users 
                WHERE last_checkin >= date('now', '-7 days')
            """)
            stats['active_users'] = cursor.fetchone()['active']

            cursor.execute("""
                SELECT COUNT(*) as new_today 
                FROM users 
                WHERE date(created_at) = date('now')
            """)
            stats['new_users_today'] = cursor.fetchone()['new_today']
            
            return stats
        finally:
            cursor.close()
            conn.close()

    def get_recent_users(self, limit: int = 10) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT user_id, username, full_name, balance, created_at, last_checkin
                FROM users
                ORDER BY COALESCE(last_checkin, created_at) DESC
                LIMIT ?
            """, (limit,))
            return list(cursor.fetchall())
        finally:
             cursor.close()
             conn.close()

    # Settings
    def get_setting(self, key: str, default: Any = None) -> Any:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            if result:
                try:
                    return json.loads(result['value'])
                except:
                    return result['value']
            return default
        except Exception:
            return default
        finally:
            cursor.close()
            conn.close()

    def set_setting(self, key: str, value: Any) -> bool:
        value_str = json.dumps(value) if not isinstance(value, str) else value
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO settings (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                """, 
                (key, value_str)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to set setting: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_invite_count(self, user_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
             cursor.execute("SELECT COUNT(*) as count FROM users WHERE invited_by = ?", (user_id,))
             return cursor.fetchone()['count']
        finally:
             cursor.close()
             conn.close()
