
import os
import logging
from database import get_database
from utils.messages import get_transaction_history_message

# Setup logging to see if any errors are logged
logging.basicConfig(level=logging.INFO)

def test_lsgd():
    os.environ['DB_TYPE'] = 'firestore'
    os.environ['ENVIRONMENT'] = 'development'
    
    db = get_database()
    user_id = 6964219489
    
    print(f"Testing /lsgd for user {user_id}")
    
    try:
        user = db.get_user(user_id)
        if not user:
            print("User not found!")
            return
            
        current_balance = user.get('balance', 0)
        print(f"Current balance: {current_balance}")
        
        transactions = db.get_user_transactions(user_id, limit=20)
        print(f"Found {len(transactions)} transactions")
        
        message = get_transaction_history_message(transactions, current_balance)
        print("Successfully generated message:")
        print("---")
        print(message)
        print("---")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lsgd()
