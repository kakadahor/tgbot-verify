"""
Database Abstract Base Class

Defines the interface that all database implementations must follow.
This ensures MySQL and Firestore implementations have the same methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class Database(ABC):
    """Abstract base class for database implementations"""

    # User Management
    @abstractmethod
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        pass

    @abstractmethod
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        pass

    @abstractmethod
    def create_user(
        self, user_id: int, username: str, full_name: str, invited_by: Optional[int] = None
    ) -> bool:
        """Add new user"""
        pass

    @abstractmethod
    def get_all_user_ids(self) -> List[int]:
        """Get all user IDs"""
        pass

    # Balance Management
    @abstractmethod
    def get_balance(self, user_id: int) -> int:
        """Get user balance"""
        pass

    @abstractmethod
    def add_balance(self, user_id: int, amount: int, description: str = "", metadata: Optional[Dict] = None, transaction_at: Optional[datetime] = None) -> bool:
        """Add Gems to user balance"""
        pass

    @abstractmethod
    def deduct_balance(self, user_id: int, amount: int, description: str = "", metadata: Optional[Dict] = None, transaction_at: Optional[datetime] = None) -> bool:
        """Deduct Gems from user balance"""
        pass

    @abstractmethod
    def log_transaction(self, user_id: int, amount: int, transaction_type: str, description: str = "", metadata: Optional[Dict] = None, transaction_at: Optional[datetime] = None) -> bool:
        """Log a transaction to the ledger"""
        pass

    # Blacklist Management
    @abstractmethod
    def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blacklisted"""
        pass

    @abstractmethod
    def block_user(self, user_id: int) -> bool:
        """Add user to blacklist"""
        pass

    @abstractmethod
    def unblock_user(self, user_id: int) -> bool:
        """Remove user from blacklist"""
        pass

    @abstractmethod
    def get_blacklist(self) -> List[Dict]:
        """Get all blacklisted users"""
        pass

    # Check-in Management
    @abstractmethod
    def can_checkin(self, user_id: int) -> bool:
        """Check if user can check in today"""
        pass

    @abstractmethod
    def checkin(self, user_id: int) -> bool:
        """Perform daily check-in"""
        pass

    # Card Key Management
    @abstractmethod
    def create_card_key(
        self,
        key_code: str,
        balance: int,
        created_by: int,
        max_uses: int = 1,
        expire_days: Optional[int] = None
    ) -> bool:
        """Create a new card key"""
        pass

    @abstractmethod
    def get_card_key_info(self, key_code: str) -> Optional[Dict]:
        """Get card key information"""
        pass

    @abstractmethod
    def use_card_key(self, key_code: str, user_id: int) -> Optional[int]:
        """Use a card key"""
        pass

    @abstractmethod
    def get_all_card_keys(self) -> List[Dict]:
        """List all card keys"""
        pass

    # Verification Management
    @abstractmethod
    def add_verification(
        self,
        user_id: int,
        verification_type: str,
        verification_url: str,
        status: str,
        result: str = "",
        verification_id: Optional[str] = ""
    ) -> bool:
        """Add verification record"""
        pass

    @abstractmethod
    def get_user_verifications(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's verification history"""
        pass

    @abstractmethod
    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's transaction history"""
        pass

    @abstractmethod
    def get_user_stats(self) -> Dict:
        """Get user statistics (total users, active users, etc.)"""
        pass

    @abstractmethod
    def get_recent_users(self, limit: int = 10) -> List[Dict]:
        """Get recent active users ordered by last activity"""
        pass

    # Settings Management
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value by key"""
        pass

    @abstractmethod
    def get_invite_count(self, user_id: int) -> int:
        """Get the number of users invited by this user"""
        pass

