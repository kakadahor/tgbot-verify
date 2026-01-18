"""MySQL Database Implementation

Using the provided MySQL server for data storage
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MySQLDatabase:
    """MySQL Database Management Class"""

    def __init__(self):
        """Initialize database connection"""
        import os
        
        # Read configuration from environment variables (recommended) or use defaults
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'tgbot_user'),
            'password': os.getenv('MYSQL_PASSWORD', 'your_password_here'),
            'database': os.getenv('MYSQL_DATABASE', 'tgbot_verify'),
            'charset': 'utf8mb4',
            'autocommit': False,
        }
        logger.info(f"MySQL Database Initialization: {self.config['user']}@{self.config['host']}/{self.config['database']}")
        self.init_database()

    def log_transaction(self, user_id: int, amount: int, transaction_type: str, description: str = "", metadata: Dict = None, transaction_at: datetime = None):
        """Log a transaction to the ledger"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute(
                """
                INSERT INTO ledger (user_id, amount, type, description, metadata, created_at, transaction_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                """,
                (user_id, amount, transaction_type, description, metadata_json, transaction_at)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def trx_exists(self, trx_id: str) -> bool:
        """Check if a transaction ID has already been processed"""
        if not trx_id:
            return False
            
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Check in ledger metadata (stored as JSON string)
            # We search for the exact trx_id in the JSON string
            pattern = f'%"{trx_id}"%'
            cursor.execute(
                "SELECT 1 FROM ledger WHERE metadata LIKE %s LIMIT 1",
                (pattern,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking trx_exists: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_connection(self):
        """Get database connection"""
        return pymysql.connect(**self.config)

    def init_database(self):
        """Initialize database table structure"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Migration: Add transaction_at to ledger if it doesn't exist
            try:
                cursor.execute("SHOW COLUMNS FROM ledger LIKE 'transaction_at'")
                if not cursor.fetchone():
                    logger.info("Migrating ledger table: adding transaction_at column")
                    cursor.execute("ALTER TABLE ledger ADD COLUMN transaction_at DATETIME NULL AFTER created_at")
                    conn.commit()
            except Exception as e:
                logger.debug(f"Migration check skipped: {e} (ledger table might not exist yet)")

            # Users Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    balance INT DEFAULT 1,
                    is_blocked TINYINT(1) DEFAULT 0,
                    invited_by BIGINT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_checkin DATETIME NULL,
                    INDEX idx_username (username),
                    INDEX idx_invited_by (invited_by)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Invitation Records Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS invitations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    inviter_id BIGINT NOT NULL,
                    invitee_id BIGINT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_inviter (inviter_id),
                    INDEX idx_invitee (invitee_id),
                    FOREIGN KEY (inviter_id) REFERENCES users(user_id),
                    FOREIGN KEY (invitee_id) REFERENCES users(user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Verification Records Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS verifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    verification_type VARCHAR(50) NOT NULL,
                    verification_url TEXT,
                    verification_id VARCHAR(255),
                    status VARCHAR(50) NOT NULL,
                    result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_type (verification_type),
                    INDEX idx_created (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Card Keys Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS card_keys (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    key_code VARCHAR(100) UNIQUE NOT NULL,
                    balance INT NOT NULL,
                    max_uses INT DEFAULT 1,
                    current_uses INT DEFAULT 0,
                    expire_at DATETIME NULL,
                    created_by BIGINT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_key_code (key_code),
                    INDEX idx_created_by (created_by)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Card Key Usage Records
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS card_key_usage (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    key_code VARCHAR(100) NOT NULL,
                    user_id BIGINT NOT NULL,
                    used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_key_code (key_code),
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Transaction Ledger Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    amount INT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    transaction_at DATETIME NULL,
                    INDEX idx_user_id (user_id),
                    INDEX idx_type (type),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            # Settings Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    `key` VARCHAR(255) PRIMARY KEY,
                    `value` TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            conn.commit()
            logger.info("MySQL database tables initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

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
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (user_id, username, full_name, invited_by),
            )

            if invited_by:
                cursor.execute(
                    "UPDATE users SET balance = balance + 2 WHERE user_id = %s",
                    (invited_by,),
                )

                cursor.execute(
                    """
                    INSERT INTO invitations (inviter_id, invitee_id, created_at)
                    VALUES (%s, %s, NOW())
                    """,
                    (invited_by, user_id),
                )

            conn.commit()
            return True

        except pymysql.err.IntegrityError:
            conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            
            if row:
                # Create a new dictionary and convert datetime to ISO format strings
                result = dict(row)
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].isoformat()
                if result.get('last_checkin'):
                    result['last_checkin'] = result['last_checkin'].isoformat()
                return result
            return None

        finally:
            cursor.close()
            conn.close()

    def user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        return self.get_user(user_id) is not None

    def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blacklisted"""
        user = self.get_user(user_id)
        return user and user["is_blocked"] == 1

    def block_user(self, user_id: int) -> bool:
        """Blacklist a user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE users SET is_blocked = 1 WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist user: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def unblock_user(self, user_id: int) -> bool:
        """Remove user from blacklist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE users SET is_blocked = 0 WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to unblock user: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_blacklist(self) -> List[Dict]:
        """Get blacklist"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute("SELECT * FROM users WHERE is_blocked = 1")
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    def add_balance(self, user_id: int, amount: int, description: str = "Balance added", metadata: Dict = None, transaction_at: datetime = None) -> bool:
        """Add credits to user balance"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (amount, user_id),
            )
            conn.commit()
            
            # Log transaction
            self.log_transaction(user_id, amount, 'topup' if amount > 5 else 'reward', description, metadata, transaction_at)
            
            return True
        except Exception as e:
            logger.error(f"Failed to add credits: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def deduct_balance(self, user_id: int, amount: int, description: str = "Balance deducted", metadata: Dict = None, transaction_at: datetime = None) -> bool:
        """Deduct credits from user balance"""
        user = self.get_user(user_id)
        if not user or user["balance"] < amount:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET balance = balance - %s WHERE user_id = %s",
                (amount, user_id),
            )
            conn.commit()
            
            # Log transaction
            self.log_transaction(user_id, -amount, 'spend', description, metadata, transaction_at)
            
            return True
        except Exception as e:
            logger.error(f"Failed to deduct credits: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def can_checkin(self, user_id: int) -> bool:
        """Check if user can check in today"""
        user = self.get_user(user_id)
        if not user:
            return False

        last_checkin = user.get("last_checkin")
        if not last_checkin:
            return True

        last_date = datetime.fromisoformat(last_checkin).date()
        today = datetime.now().date()

        return last_date < today

    def checkin(self, user_id: int) -> bool:
        """User check-in (prevents double check-in)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Use SQL atomic operation to avoid race conditions
            # Only update if last_checkin is NULL or date < today
            cursor.execute(
                """
                UPDATE users
                SET balance = balance + 1, last_checkin = NOW()
                WHERE user_id = %s 
                AND (
                    last_checkin IS NULL 
                    OR DATE(last_checkin) < CURDATE()
                )
                """,
                (user_id,),
            )
            conn.commit()
            
            # Check if updated (affected_rows > 0 indicates success)
            success = cursor.rowcount > 0
            return success
            
        except Exception as e:
            logger.error(f"Check-in failed: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def add_verification(
        self, user_id: int, verification_type: str, verification_url: str,
        status: str, result: str = "", verification_id: str = ""
    ) -> bool:
        """Add verification record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO verifications
                (user_id, verification_type, verification_url, verification_id, status, result, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (user_id, verification_type, verification_url, verification_id, status, result),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add verification record: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def get_user_verifications(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user verification records"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute(
                """
                SELECT * FROM verifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user transaction history from ledger"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute(
                """
                SELECT * FROM ledger
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            results = list(cursor.fetchall())
            
            # Convert datetime objects to ISO format strings
            for row in results:
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()
                if row.get('transaction_at'):
                    row['transaction_at'] = row['transaction_at'].isoformat()
            
            return results
        finally:
            cursor.close()
            conn.close()

    def create_card_key(
        self, key_code: str, balance: int, created_by: int,
        max_uses: int = 1, expire_days: Optional[int] = None
    ) -> bool:
        """Create a card key"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            expire_at = None
            if expire_days:
                expire_at = datetime.now() + timedelta(days=expire_days)

            cursor.execute(
                """
                INSERT INTO card_keys (key_code, balance, max_uses, created_by, created_at, expire_at)
                VALUES (%s, %s, %s, %s, NOW(), %s)
                """,
                (key_code, balance, max_uses, created_by, expire_at),
            )
            conn.commit()
            return True

        except pymysql.err.IntegrityError:
            logger.error(f"Card key already exists: {key_code}")
            conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Failed to create card key: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def use_card_key(self, key_code: str, user_id: int) -> Optional[int]:
        """Use a card key, returns the amount of credits earned"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            # Query card key
            cursor.execute(
                "SELECT * FROM card_keys WHERE key_code = %s",
                (key_code,),
            )
            card = cursor.fetchone()

            if not card:
                return None

            # Check if expired
            if card["expire_at"] and datetime.now() > card["expire_at"]:
                return -2

            # Check max uses
            if card["current_uses"] >= card["max_uses"]:
                return -1

            # Check if user has already used this key
            cursor.execute(
                "SELECT COUNT(*) as count FROM card_key_usage WHERE key_code = %s AND user_id = %s",
                (key_code, user_id),
            )
            count = cursor.fetchone()
            if count['count'] > 0:
                return -3

            # Update usage count
            cursor.execute(
                "UPDATE card_keys SET current_uses = current_uses + 1 WHERE key_code = %s",
                (key_code,),
            )

            # Record usage
            cursor.execute(
                "INSERT INTO card_key_usage (key_code, user_id, used_at) VALUES (%s, %s, NOW())",
                (key_code, user_id),
            )

            # Add credits to user
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE user_id = %s",
                (card["balance"], user_id),
            )

            conn.commit()
            return card["balance"]

        except Exception as e:
            logger.error(f"Failed to use card key: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    def get_card_key_info(self, key_code: str) -> Optional[Dict]:
        """Get card key information"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute("SELECT * FROM card_keys WHERE key_code = %s", (key_code,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_all_card_keys(self, created_by: Optional[int] = None) -> List[Dict]:
        """Get all card keys (can filter by creator)"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            if created_by:
                cursor.execute(
                    "SELECT * FROM card_keys WHERE created_by = %s ORDER BY created_at DESC",
                    (created_by,),
                )
            else:
                cursor.execute("SELECT * FROM card_keys ORDER BY created_at DESC")
            
            return list(cursor.fetchall())
        finally:
            cursor.close()
            conn.close()

    def get_all_user_ids(self) -> List[int]:
        """Get all user IDs"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT user_id FROM users")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            cursor.close()
            conn.close()

    def get_user_stats(self) -> Dict:
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            stats = {}
            
            # Total users
            cursor.execute("SELECT COUNT(*) as total FROM users")
            stats['total_users'] = cursor.fetchone()['total']
            
            # Active users (checked in within last 7 days)
            cursor.execute("""
                SELECT COUNT(*) as active 
                FROM users 
                WHERE last_checkin >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """)
            stats['active_users'] = cursor.fetchone()['active']
            
            # Total gems in circulation
            cursor.execute("SELECT SUM(balance) as total_gems FROM users")
            stats['total_gems'] = cursor.fetchone()['total_gems'] or 0
            
            # Blocked users
            cursor.execute("SELECT COUNT(*) as blocked FROM users WHERE is_blocked = 1")
            stats['blocked_users'] = cursor.fetchone()['blocked']
            
            # New users today
            cursor.execute("""
                SELECT COUNT(*) as new_today 
                FROM users 
                WHERE DATE(created_at) = CURDATE()
            """)
            stats['new_users_today'] = cursor.fetchone()['new_today']
            
            return stats
        finally:
            cursor.close()
            conn.close()

    def get_recent_users(self, limit: int = 10) -> List[Dict]:
        """Get recent active users ordered by last check-in or creation date"""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor)

        try:
            cursor.execute("""
                SELECT user_id, username, full_name, balance, created_at, last_checkin
                FROM users
                ORDER BY COALESCE(last_checkin, created_at) DESC
                LIMIT %s
            """, (limit,))
            
            results = list(cursor.fetchall())
            
            # Convert datetime objects to ISO format strings
            for row in results:
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()
                if row.get('last_checkin'):
                    row['last_checkin'] = row['last_checkin'].isoformat()
            
            return results
        finally:
            cursor.close()
            conn.close()

    # ========== Settings Management ==========

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(DictCursor)
            
            cursor.execute("SELECT `value` FROM settings WHERE `key` = %s", (key,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                import json
                try:
                    return json.loads(result['value'])
                except:
                    return result['value']
            return default
        except Exception as e:
            logger.error(f"Failed to get setting {key}: {e}")
            return default

    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value by key"""
        try:
            import json
            # Only json dumps if not a string
            value_str = json.dumps(value) if not isinstance(value, str) else value
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO settings (`key`, `value`) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE `value` = %s
            """
            cursor.execute(query, (key, value_str, value_str))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")
            return False

    def get_invite_count(self, user_id: int) -> int:
        """Get the number of users invited by this user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE invited_by = %s", (user_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Failed to get invite count for {user_id}: {e}")
            return 0


# Create alias for global instance to maintain compatibility with SQLite version
Database = MySQLDatabase


