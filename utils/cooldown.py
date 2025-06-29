
import time
from utils.data_manager import read_json, write_json

COOLDOWN_FILE = "data/cooldowns.json"
COOLDOWN_SECONDS = 10

def can_play(user_id):
    """Check if user can play (cooldown expired)"""
    cooldowns = read_json(COOLDOWN_FILE)
    user_key = str(user_id)
    current_time = time.time()
    
    if user_key in cooldowns:
        last_play = cooldowns[user_key]
        time_left = COOLDOWN_SECONDS - (current_time - last_play)
        if time_left > 0:
            return False, time_left
    
    # Update cooldown
    cooldowns[user_key] = current_time
    write_json(COOLDOWN_FILE, cooldowns)
    return True, 0
