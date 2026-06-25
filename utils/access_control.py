import json
import os

# Define path for access controls file inside the project directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
ACCESS_FILE = os.path.join(DATA_DIR, 'access.json')

def load_access():
    """Loads current access control configurations from JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ACCESS_FILE):
        default_data = {"allowed_users": [], "blocked_users": []}
        save_access(default_data)
        return default_data
    try:
        with open(ACCESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"allowed_users": [], "blocked_users": []}

def save_access(data):
    """Saves access control configurations to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(ACCESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving access list: {e}")

def is_user_allowed(user_id: int, is_admin: bool) -> bool:
    """Checks if a user is allowed to run commands based on whitelist/blacklist."""
    # Server/Guild Administrators are always allowed bypass permissions
    if is_admin:
        return True
        
    data = load_access()
    user_str = str(user_id)

    # 1. Check blacklist (blocked users)
    if user_str in data.get("blocked_users", []) or user_id in data.get("blocked_users", []):
        return False

    # 2. Check whitelist (allowed users)
    allowed_list = data.get("allowed_users", [])
    if not allowed_list:
        # If the allowlist is empty, everyone who isn't explicitly blocked is allowed
        return True

    return user_str in allowed_list or user_id in allowed_list
