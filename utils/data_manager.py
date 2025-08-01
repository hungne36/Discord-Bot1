import json, os
from datetime import datetime

DATA_FILE = "data/sodu.json"
HISTORY_FILE = "data/lichsu.json"
USER_DATA_FILE = "data/user_data.json"
PHUCLOI_FILE = "data/pending_rewards.json"

os.makedirs("data", exist_ok=True)

for path, default in [
    (DATA_FILE, {}),
    (HISTORY_FILE, []),
    (USER_DATA_FILE, {}),
    (PHUCLOI_FILE, {})
]:
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(default, f, indent=2)

def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        if "sodu" in path:
            return {}
        elif "lichsu" in path:
            return []
        elif "user_data" in path:
            return {}
        else:
            return {}

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        os.fsync(f.fileno())

def get_balance(uid):
    data = read_json(DATA_FILE)
    return data.get(str(uid), 1000)

def update_balance(uid, amount):
    uid = str(uid)
    data = read_json(DATA_FILE)
    data[uid] = data.get(uid, 0) + amount
    write_json(DATA_FILE, data)
    return data[uid]

def add_balance(uid, amount):
    """Alias for update_balance for backward compatibility"""
    return update_balance(uid, amount)

def get_user_history(uid, limit=None):
    hist = read_json(HISTORY_FILE)
    user_hist = [h for h in hist if h["user_id"] == uid]
    return user_hist[-limit:] if limit else user_hist

def add_history(uid, action, amount, balance, username=None):
    hist = read_json(HISTORY_FILE)
    entry = {
        "user_id": uid,
        "action": action,
        "amount": amount,
        "balance_after": balance,
        "timestamp": datetime.utcnow().isoformat() + "Z"  # ✅ ISO UTC
    }
    if username:
        entry["username"] = username
    hist.append(entry)
    write_json(HISTORY_FILE, hist)

def get_pet_buff(uid: int) -> float:
    data = read_json("data/pets.json")
    return data.get(str(uid), {}).get("last", (None,None,0))[2] or 0

def get_today_spent(uid):
    """Get total amount spent today by user"""
    hist = read_json(HISTORY_FILE)
    today = datetime.utcnow().date()
    spent = 0
    for h in hist:
        if h["user_id"] == uid:
            try:
                amount = int(h["amount"]) if isinstance(h["amount"], (int, str)) and str(h["amount"]).lstrip('-').isdigit() else 0
                if amount < 0:
                    entry_date = datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date()
                    if entry_date == today:
                        spent += abs(amount)
            except (ValueError, TypeError):
                continue
    return spent

def get_today_net(uid):
    """Get net gain/loss today for user (positive = gained, negative = lost)"""
    hist = read_json(HISTORY_FILE)
    today = datetime.utcnow().date()
    net = 0
    for h in hist:
        if h["user_id"] == uid:
            try:
                amount = int(h["amount"]) if isinstance(h["amount"], (int, str)) and str(h["amount"]).lstrip('-').isdigit() else 0
                entry_date = datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date()
                if entry_date == today:
                    net += amount
            except (ValueError, TypeError):
                continue
    return net

def get_pending_reward(uid):
    """Get pending reward amount for user"""
    pending_data = read_json(PHUCLOI_FILE)
    return pending_data.get(str(uid), 0)

def get_username(user):
    """Get username from Discord user object"""
    return user.display_name if hasattr(user, 'display_name') else str(user)

def update_today_spent(uid, amount):
    """Update today's spent amount - this is tracked via history"""
    # This is handled automatically through add_history when balance is reduced
    pass

def get_pet_bonus_percent(uid):
    """Get pet bonus percentage for user"""
    return get_pet_buff(uid)

def log_history(uid, action, amount):
    """Log game history - wrapper for add_history"""
    balance = get_balance(uid)
    add_history(uid, action, amount, balance)

def get_pet_bonus(uid, amount):
    """Get pet bonus amount based on user's pet buff"""
    buff_percent = get_pet_buff(uid)
    return int(amount * buff_percent / 100) if buff_percent > 0 else 0