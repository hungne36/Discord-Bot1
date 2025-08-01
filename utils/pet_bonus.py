
from utils.data_manager import get_pet_buff

def get_pet_bonus_multiplier(user_id):
    """Get pet bonus multiplier for user"""
    buff_percent = get_pet_buff(user_id)
    return buff_percent / 100 if buff_percent > 0 else 0

def calculate_pet_bonus(user_id, base_amount):
    """Calculate bonus amount based on user's pet"""
    multiplier = get_pet_bonus_multiplier(user_id)
    return int(base_amount * multiplier)
