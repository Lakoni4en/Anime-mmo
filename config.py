"""
⚙️ Конфигурация текстовой MMO RPG
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============ TELEGRAM ============
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
_admin_id = os.getenv("ADMIN_ID", "0")
try:
    ADMIN_ID = int(_admin_id)
except ValueError:
    ADMIN_ID = 0

# ============ БАЗА ДАННЫХ ============
DATABASE_PATH = "rpg_game.db"

# ============ ЭНЕРГИЯ ============
MAX_ENERGY = 100
HUNT_ENERGY_COST = 10
ENERGY_REGEN_MINUTES = 3       # 1 энергия за 3 минуты (полная за 5 часов)

# ============ АРЕНА ============
ARENA_FIGHTS_PER_DAY = 5
ARENA_WIN_GOLD = 200
ARENA_WIN_CRYSTALS = 3
ARENA_WIN_RATING = 15
ARENA_LOSE_RATING = 10

# ============ ЕЖЕДНЕВНЫЙ БОНУС ============
DAILY_GOLD = 100
DAILY_CRYSTALS = 5
DAILY_ENERGY = 30

# ============ TELEGRAM STARS МАГАЗИН ============
STARS_SHOP = {
    "crystals_50": {"crystals": 50, "stars": 25, "label": "50 💎 Кристаллов"},
    "crystals_150": {"crystals": 150, "stars": 65, "label": "150 💎 Кристаллов", "bonus": "+15 бонус"},
    "crystals_500": {"crystals": 500, "stars": 200, "label": "500 💎 Кристаллов", "bonus": "+75 бонус"},
    "energy_full": {"energy": MAX_ENERGY, "stars": 10, "label": f"⚡ {MAX_ENERGY} Энергии"},
}

# ============ УРОВЕНЬ ============
CRYSTALS_PER_LEVELUP = 10     # Кристаллы за повышение уровня
GOLD_PER_LEVELUP = 200        # Золото за повышение уровня
