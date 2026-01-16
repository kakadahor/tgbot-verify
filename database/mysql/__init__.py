"""MySQL Database Implementation"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the existing MySQL database class
from database_mysql import MySQLDatabase

# Re-export it directly
__all__ = ['MySQLDatabase']

# For backwards compatibility and factory use
MySQLDatabaseWrapper = MySQLDatabase
