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