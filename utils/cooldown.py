
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
import time

# Dictionary to store last play time for each user
last_play_times = {}

def can_play(user_id, cooldown_seconds=3):
    """
    Check if a user can play (not in cooldown).
    
    Args:
        user_id: The user's Discord ID
        cooldown_seconds: Cooldown duration in seconds (default 3)
    
    Returns:
        tuple: (can_play: bool, wait_time: float)
    """
    current_time = time.time()
    user_id = str(user_id)
    
    if user_id not in last_play_times:
        last_play_times[user_id] = current_time
        return True, 0
    
    time_since_last = current_time - last_play_times[user_id]
    
    if time_since_last >= cooldown_seconds:
        last_play_times[user_id] = current_time
        return True, 0
    else:
        wait_time = cooldown_seconds - time_since_last
        return False, wait_time
