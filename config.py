"""
⚙️ Конфигурация текстовой MMO RPG v2
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
_admin_id = os.getenv("ADMIN_ID", "0")
try:
    ADMIN_ID = int(_admin_id)
except ValueError:
    ADMIN_ID = 0

DATABASE_PATH = "rpg_game.db"

# Энергия
MAX_ENERGY = 100
HUNT_ENERGY_COST = 10
ENERGY_REGEN_MINUTES = 3

# Арена
ARENA_FIGHTS_PER_DAY = 5
ARENA_WIN_GOLD = 200
ARENA_WIN_CRYSTALS = 3
ARENA_WIN_RATING = 15
ARENA_LOSE_RATING = 10

# Башня
TOWER_ATTEMPTS_PER_DAY = 3

# Ежедневный бонус
DAILY_GOLD = 100
DAILY_CRYSTALS = 5

# Уровень
CRYSTALS_PER_LEVELUP = 10
GOLD_PER_LEVELUP = 200

# Аукцион
AUCTION_MAX_LISTINGS = 3
AUCTION_EXPIRE_HOURS = 24

# Stars магазин
STARS_SHOP = {
    "crystals_50": {"crystals": 50, "stars": 25, "label": "50 💎 Кристаллов"},
    "crystals_150": {"crystals": 150, "stars": 65, "label": "150 💎 Кристаллов"},
    "crystals_500": {"crystals": 500, "stars": 200, "label": "500 💎 Кристаллов"},
    "energy_full": {"energy": MAX_ENERGY, "stars": 10, "label": f"⚡ {MAX_ENERGY} Энергии"},
}
