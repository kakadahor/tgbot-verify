"""
Database Factory

This module provides a factory function to create the appropriate database instance
based on configuration. This allows easy switching between MySQL and Firestore.

Usage:
    from database import get_database
    
    db = get_database()  # Automatically selects based on DB_TYPE env variable
"""

import os
from typing import Optional
from database.base import Database as DatabaseInterface

# Cache the database instance (singleton pattern)
_db_instance: Optional[DatabaseInterface] = None


def get_database(db_type: Optional[str] = None) -> DatabaseInterface:
    """
    Get database instance based on configuration
    
    Args:
        db_type: Database type ('mysql' or 'firestore'). 
                If None, reads from DB_TYPE environment variable.
                Defaults to 'mysql' if not specified.
    
    Returns:
        Database instance (MySQL or Firestore)
    
    Environment Variables:
        DB_TYPE: 'mysql' or 'firestore' (default: 'mysql')
        
    Examples:
        # Use environment variable
        export DB_TYPE=firestore
        db = get_database()
        
        # Or specify directly
        db = get_database('mysql')
        db = get_database('firestore')
    """
    global _db_instance
    
    # Return cached instance if available
    if _db_instance is not None:
        return _db_instance
    
    # Determine database type
    if db_type is None:
        db_type = os.getenv('DB_TYPE', 'mysql').lower()
    
    # Create appropriate database instance
    if db_type == 'mysql':
        from database.mysql import MySQLDatabaseWrapper
        _db_instance = MySQLDatabaseWrapper()
        print(f"✅ Using MySQL database")
    
    elif db_type == 'firestore':
        from database.firestore import FirestoreDatabase
        _db_instance = FirestoreDatabase()
        print(f"✅ Using Firestore database")

    elif db_type == 'sqlite':
        from database.sqlite import SQLiteDatabase
        _db_instance = SQLiteDatabase()
        print(f"✅ Using SQLite database")
    
    else:
        raise ValueError(f"Unknown database type: {db_type}. Use 'mysql' or 'firestore'")
    
    return _db_instance


def reset_database():
    """Reset the cached database instance (useful for testing)"""
    global _db_instance
    _db_instance = None


# Convenience exports
__all__ = ['get_database', 'reset_database', 'DatabaseInterface']
