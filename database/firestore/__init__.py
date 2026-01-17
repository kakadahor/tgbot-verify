"""
Firestore Database Implementation

This implementation uses Google Cloud Firestore instead of MySQL.
All methods match the Database interface defined in database/base.py
"""

from database.base import Database
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

try:
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    logger.warning("Firestore library not installed. Run: pip install google-cloud-firestore")


class FirestoreDatabase(Database):
    """Firestore Database Implementation"""
    
    def __init__(self):
        """Initialize Firestore database"""
        if not FIRESTORE_AVAILABLE:
            raise ImportError("google-cloud-firestore is not installed")
        
        self.db = firestore.Client()
        
        # Collection references (Multi-Environment aware)
        from config import FS_COLLECTIONS
        self.users_ref = self.db.collection(FS_COLLECTIONS['users'])
        self.verifications_ref = self.db.collection(FS_COLLECTIONS['verifications'])
        self.card_keys_ref = self.db.collection(FS_COLLECTIONS['card_keys'])
        self.card_usage_ref = self.db.collection(FS_COLLECTIONS['card_key_usage'])
        self.invitations_ref = self.db.collection(FS_COLLECTIONS['invitations'])
        self.ledger_ref = self.db.collection(FS_COLLECTIONS['ledger'])
        
        logger.info(f"Firestore database initialized (Env: {FS_COLLECTIONS['users']})")
    
    # ========== Transaction Ledger ==========
    
    def log_transaction(self, user_id: int, amount: int, transaction_type: str, description: str = "", metadata: Dict = None, transaction_at: datetime = None):
        """Log a transaction to the Firestore ledger"""
        try:
            transaction_data = {
                'user_id': user_id,
                'amount': amount,
                'type': transaction_type,
                'description': description,
                'metadata': metadata or {},
                'created_at': firestore.SERVER_TIMESTAMP,
                'transaction_at': transaction_at or firestore.SERVER_TIMESTAMP
            }
            from config import FS_COLLECTIONS
            self.db.collection(FS_COLLECTIONS['ledger']).add(transaction_data)
            return True
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}")
            return False
    
    # ========== User Management ==========
    
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        doc = self.users_ref.document(str(user_id)).get()
        return doc.exists
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        doc = self.users_ref.document(str(user_id)).get()
        if doc.exists:
            data = doc.to_dict()
            data['user_id'] = user_id  # Add user_id to the dict
            
            # Convert timestamps to ISO format strings for parity with MySQL implementation
            for key in ['created_at', 'last_checkin', 'expire_at']:
                if key in data and data[key]:
                    # Some data might already be strings if manually entered or from older records
                    if hasattr(data[key], 'isoformat'):
                        data[key] = data[key].isoformat()
            
            return data
        return None
    
    def create_user(
        self, user_id: int, username: str, full_name: str, invited_by: Optional[int] = None
    ) -> bool:
        """Add new user"""
        try:
            # Check if already exists (Integrity check)
            if self.user_exists(user_id):
                return False

            # Create user document
            self.users_ref.document(str(user_id)).set({
                'username': username,
                'full_name': full_name,
                'balance': 1,  # Initial registration reward
                'is_blocked': False,
                'last_checkin': None,
                'invited_by': invited_by,
                'created_at': firestore.SERVER_TIMESTAMP,
            })

            # Handle invitation reward
            if invited_by and self.user_exists(invited_by):
                # Reward inviter with 2 Gems
                self.add_balance(invited_by, 2)
                
                # Record invitation
                self.invitations_ref.add({
                    'inviter_id': invited_by,
                    'invited_id': user_id,
                    'created_at': firestore.SERVER_TIMESTAMP,
                })

            logger.info(f"User {user_id} registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False
    
    def get_all_user_ids(self) -> List[int]:
        """Get all user IDs"""
        docs = self.users_ref.stream()
        return [int(doc.id) for doc in docs]
    
    # ========== Balance Management ==========
    
    def get_balance(self, user_id: int) -> int:
        """Get user balance"""
        user = self.get_user(user_id)
        return user['balance'] if user else 0
    
    def add_balance(self, user_id: int, amount: int, description: str = "Balance added", metadata: Dict = None, transaction_at: datetime = None, txn_type: str = 'reward') -> bool:
        """Add Gems to user balance"""
        try:
            user_ref = self.users_ref.document(str(user_id))
            user_ref.update({
                'balance': firestore.Increment(amount)
            })
            self.log_transaction(user_id, amount, txn_type, description, metadata, transaction_at)
            return True
        except Exception as e:
            logger.error(f"Failed to add balance: {e}")
            return False
    
    def deduct_balance(self, user_id: int, amount: int, description: str = "Balance deducted", metadata: Dict = None, transaction_at: datetime = None) -> bool:
        """Deduct Gems from user balance"""
        user = self.get_user(user_id)
        if not user or user['balance'] < amount:
            return False
        
        try:
            user_ref = self.users_ref.document(str(user_id))
            user_ref.update({
                'balance': firestore.Increment(-amount)
            })
            self.log_transaction(user_id, -amount, 'spend', description, metadata, transaction_at)
            return True
        except Exception as e:
            logger.error(f"Failed to deduct balance: {e}")
            return False
    
    # ========== Blacklist Management ==========
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blacklisted"""
        user = self.get_user(user_id)
        return user['is_blocked'] if user else False
    
    def block_user(self, user_id: int) -> bool:
        """Add user to blacklist"""
        try:
            self.users_ref.document(str(user_id)).update({
                'is_blocked': True
            })
            return True
        except Exception as e:
            logger.error(f"Failed to block user: {e}")
            return False
    
    def unblock_user(self, user_id: int) -> bool:
        """Remove user from blacklist"""
        try:
            self.users_ref.document(str(user_id)).update({
                'is_blocked': False
            })
            return True
        except Exception as e:
            logger.error(f"Failed to unblock user: {e}")
            return False
    
    def get_blacklist(self) -> List[Dict]:
        """Get all blacklisted users"""
        docs = self.users_ref.where(filter=FieldFilter('is_blocked', '==', True)).stream()
        return [{'user_id': int(doc.id), **doc.to_dict()} for doc in docs]
    
    # ========== Check-in Management ==========
    
    def can_checkin(self, user_id: int) -> bool:
        """Check if user can check in today (Cambodia Time UTC+7)"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        last_checkin = user.get('last_checkin')
        if not last_checkin:
            return True
        
        # Cambodia Timezone (UTC+7)
        kh_tz = timezone(timedelta(hours=7))
        
        # Convert last_checkin to KH date
        if isinstance(last_checkin, str):
            # Parse ISO string and move to KH timezone
            dt = datetime.fromisoformat(last_checkin)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            last_date_kh = dt.astimezone(kh_tz).date()
        elif hasattr(last_checkin, 'timestamp'):
            # Convert timestamp to KH date
            dt = datetime.fromtimestamp(last_checkin.timestamp(), tz=timezone.utc)
            last_date_kh = dt.astimezone(kh_tz).date()
        else:
            return True
        
        # Current date in Cambodia
        today_kh = datetime.now(kh_tz).date()
        return last_date_kh < today_kh
    
    def checkin(self, user_id: int) -> bool:
        """Perform daily check-in"""
        if not self.can_checkin(user_id):
            return False
        
        try:
            user_ref = self.users_ref.document(str(user_id))
            user_ref.update({
                'last_checkin': firestore.SERVER_TIMESTAMP,
                'balance': firestore.Increment(1)
            })
            self.log_transaction(user_id, 1, 'checkin', 'Daily check-in')
            return True
        except Exception as e:
            logger.error(f"Check-in failed: {e}")
            return False
    
    # ========== Card Key Management ==========
    
    def create_card_key(
        self,
        key_code: str,
        balance: int,
        created_by: int,
        max_uses: int = 1,
        expire_days: Optional[int] = None
    ) -> bool:
        """Create a new card key"""
        try:
            expire_at = None
            if expire_days:
                expire_at = datetime.now() + timedelta(days=expire_days)
            
            self.card_keys_ref.document(key_code).set({
                'balance': balance,
                'max_uses': max_uses,
                'current_uses': 0,
                'created_by': created_by,
                'expire_at': expire_at,
                'created_at': firestore.SERVER_TIMESTAMP,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create card key: {e}")
            return False
    
    def get_card_key_info(self, key_code: str) -> Optional[Dict]:
        """Get card key information"""
        doc = self.card_keys_ref.document(key_code).get()
        if doc.exists:
            data = doc.to_dict()
            data['key_code'] = key_code
            
            # Convert timestamps to ISO strings
            if data.get('expire_at') and hasattr(data['expire_at'], 'isoformat'):
                data['expire_at'] = data['expire_at'].isoformat()
            if data.get('created_at') and hasattr(data['created_at'], 'isoformat'):
                data['created_at'] = data['created_at'].isoformat()
                
            return data
        return None
    
    def use_card_key(self, key_code: str, user_id: int) -> Optional[int]:
        """Use a card key, returns the amount of Gems earned or error code"""
        # Check if key exists
        key = self.get_card_key_info(key_code)
        if not key:
            return None # Match MySQL: return None if key not found
        
        # Check if expired
        if key.get('expire_at'):
            expire_at = key['expire_at']
            if isinstance(expire_at, str):
                expire_at = datetime.fromisoformat(expire_at)
            elif hasattr(expire_at, 'timestamp'):
                expire_at = datetime.fromtimestamp(expire_at.timestamp())
                
            if datetime.now() > expire_at:
                return -2 # Match MySQL: -2 for expired
        
        # Check max uses
        if key['current_uses'] >= key['max_uses']:
            return -1 # Match MySQL: -1 for max uses
        
        # Check if user already used this key
        usage_query = self.card_usage_ref.where(filter=FieldFilter('user_id', '==', user_id)).where(filter=FieldFilter('key_code', '==', key_code)).limit(1).get()
        if len(list(usage_query)) > 0:
            return -3 # Match MySQL: -3 for already used
        
        # Use the key
        try:
            # Add Gems to user
            self.add_balance(user_id, key['balance'])
            
            # Increment usage count
            self.card_keys_ref.document(key_code).update({
                'current_uses': firestore.Increment(1)
            })
            
            # Record usage
            self.card_usage_ref.add({
                'user_id': user_id,
                'key_code': key_code,
                'Gems': key['balance'],
                'used_at': firestore.SERVER_TIMESTAMP,
            })
            
            return key['balance']
        except Exception as e:
            logger.error(f"Failed to use card key: {e}")
            return None
    
    def get_all_card_keys(self) -> List[Dict]:
        """List all card keys"""
        docs = self.card_keys_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        return [{'key_code': doc.id, **doc.to_dict()} for doc in docs]
    
    # ========== Verification Management ==========
    
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
        try:
            self.verifications_ref.add({
                'user_id': user_id,
                'verification_type': verification_type,
                'verification_url': verification_url,
                'status': status,
                'result': result,
                'verification_id': verification_id,
                'created_at': firestore.SERVER_TIMESTAMP,
            })
            return True
        except Exception as e:
            logger.error(f"Failed to add verification: {e}")
            return False
    
    def get_user_verifications(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's verification history"""
        docs = (self.verifications_ref
                .where(filter=FieldFilter('user_id', '==', user_id))
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream())
        
        verifications = []
        for doc in docs:
            data = doc.to_dict()
            
            # Convert timestamps to ISO strings
            if data.get('created_at') and hasattr(data['created_at'], 'isoformat'):
                data['created_at'] = data['created_at'].isoformat()
            
            verifications.append(data)
        
        logger.info(f"Retrieved {len(verifications)} verifications for user {user_id}")
        return verifications

    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's transaction history from ledger"""
        docs = (self.ledger_ref
                .where(filter=FieldFilter('user_id', '==', user_id))
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream())
        
        transactions = []
        for doc in docs:
            data = doc.to_dict()
            
            # Convert timestamps to ISO strings
            if data.get('created_at') and hasattr(data['created_at'], 'isoformat'):
                data['created_at'] = data['created_at'].isoformat()
            
            transactions.append(data)
        
        logger.info(f"Retrieved {len(transactions)} transactions for user {user_id}")
        return transactions

    def trx_exists(self, trx_id: str) -> bool:
        """Check if a transaction ID has already been processed"""
        try:
            # Use ledger_ref which is already defined in __init__
            query = self.ledger_ref.where(filter=FieldFilter('trx_id', '==', trx_id)).limit(1).get()
            return len(list(query)) > 0
        except Exception as e:
            logger.error(f"Error checking trx existence: {e}")
            return False
