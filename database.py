"""
🗄 База данных MMO RPG v2
Игроки, инвентарь, квесты, башня, экспедиции, аукцион
"""
import aiosqlite
from datetime import datetime, timedelta
from config import DATABASE_PATH, MAX_ENERGY, ENERGY_REGEN_MINUTES


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY, username TEXT DEFAULT '', first_name TEXT DEFAULT '',
            class TEXT DEFAULT '', level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0,
            gold INTEGER DEFAULT 500, crystals INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 100, max_energy INTEGER DEFAULT 100, energy_updated_at TEXT DEFAULT '',
            arena_rating INTEGER DEFAULT 1000, arena_wins INTEGER DEFAULT 0, arena_losses INTEGER DEFAULT 0,
            arena_fights_today INTEGER DEFAULT 0, arena_last_reset TEXT DEFAULT '',
            total_hunts INTEGER DEFAULT 0, total_kills INTEGER DEFAULT 0,
            tower_floor INTEGER DEFAULT 0, tower_attempts_today INTEGER DEFAULT 0, tower_last_reset TEXT DEFAULT '',
            wheel_last_spin TEXT DEFAULT '',
            daily_streak INTEGER DEFAULT 0, last_daily TEXT DEFAULT '',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            item_type TEXT, name TEXT, rarity TEXT,
            bonus_attack INTEGER DEFAULT 0, bonus_defense INTEGER DEFAULT 0,
            bonus_hp INTEGER DEFAULT 0, bonus_crit REAL DEFAULT 0,
            is_equipped INTEGER DEFAULT 0, obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            quest_type TEXT, description TEXT, target INTEGER, progress INTEGER DEFAULT 0,
            reward_gold INTEGER DEFAULT 0, reward_crystals INTEGER DEFAULT 0, reward_xp INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0, is_claimed INTEGER DEFAULT 0, date TEXT
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS expeditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            exp_type TEXT, duration_minutes INTEGER, started_at TEXT,
            reward_gold INTEGER DEFAULT 0, reward_xp INTEGER DEFAULT 0,
            reward_crystals INTEGER DEFAULT 0, reward_item_rarity TEXT DEFAULT '',
            is_collected INTEGER DEFAULT 0
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS auction (
            id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER,
            item_name TEXT, item_type TEXT, item_rarity TEXT,
            item_attack INTEGER DEFAULT 0, item_defense INTEGER DEFAULT 0,
            item_hp INTEGER DEFAULT 0, item_crit REAL DEFAULT 0,
            price INTEGER, listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.commit()


# ======== ИГРОКИ ========
async def get_player(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def create_player(user_id, username, first_name, class_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("INSERT OR IGNORE INTO players (user_id,username,first_name,class,energy_updated_at) VALUES (?,?,?,?,?)",
                         (user_id, username, first_name, class_id, now))
        await db.commit()

async def update_player_name(user_id, username, first_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET username=?,first_name=? WHERE user_id=?", (username, first_name, user_id))
        await db.commit()

# ======== ЭНЕРГИЯ ========
def calculate_energy(player):
    stored, max_e = player["energy"], player["max_energy"]
    if stored >= max_e: return max_e
    updated = player.get("energy_updated_at", "")
    if not updated: return stored
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(updated)).total_seconds() / 60.0
        return min(max_e, stored + int(elapsed / ENERGY_REGEN_MINUTES))
    except: return stored

async def spend_energy(user_id, amount, current):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET energy=?,energy_updated_at=? WHERE user_id=?", (current - amount, now, user_id))
        await db.commit()

async def set_energy(user_id, amount):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET energy=?,energy_updated_at=? WHERE user_id=?", (amount, now, user_id))
        await db.commit()

# ======== РЕСУРСЫ ========
async def add_gold(user_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (amount, user_id)); await db.commit()

async def add_crystals(user_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET crystals=crystals+? WHERE user_id=?", (amount, user_id)); await db.commit()

async def spend_gold(user_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT gold FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount: return False
        await db.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (amount, user_id)); await db.commit()
        return True

async def spend_crystals(user_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT crystals FROM players WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount: return False
        await db.execute("UPDATE players SET crystals=crystals-? WHERE user_id=?", (amount, user_id)); await db.commit()
        return True

# ======== XP ========
async def add_xp(user_id, xp):
    from game_data import xp_for_level
    player = await get_player(user_id)
    if not player: return []
    cur_xp, cur_lvl, new_levels = player["xp"] + xp, player["level"], []
    while cur_xp >= xp_for_level(cur_lvl):
        cur_xp -= xp_for_level(cur_lvl); cur_lvl += 1; new_levels.append(cur_lvl)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET xp=?,level=? WHERE user_id=?", (cur_xp, cur_lvl, user_id)); await db.commit()
    return new_levels

async def record_hunt(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET total_hunts=total_hunts+1,total_kills=total_kills+1 WHERE user_id=?", (user_id,))
        await db.commit()

# ======== АРЕНА ========
async def get_arena_fights_left(user_id):
    from config import ARENA_FIGHTS_PER_DAY
    player = await get_player(user_id)
    if not player: return 0
    today = datetime.now().strftime("%Y-%m-%d")
    if player["arena_last_reset"] != today:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE players SET arena_fights_today=0,arena_last_reset=? WHERE user_id=?", (today, user_id))
            await db.commit()
        return ARENA_FIGHTS_PER_DAY
    return max(0, ARENA_FIGHTS_PER_DAY - player["arena_fights_today"])

async def record_arena_fight(user_id, won, rating_change):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if won:
            await db.execute("UPDATE players SET arena_wins=arena_wins+1,arena_fights_today=arena_fights_today+1,arena_rating=MAX(0,arena_rating+?) WHERE user_id=?", (rating_change, user_id))
        else:
            await db.execute("UPDATE players SET arena_losses=arena_losses+1,arena_fights_today=arena_fights_today+1,arena_rating=MAX(0,arena_rating-?) WHERE user_id=?", (abs(rating_change), user_id))
        await db.commit()

async def get_arena_opponent(user_id):
    player = await get_player(user_id)
    if not player: return None
    lvl = player["level"]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM players WHERE user_id!=? AND class!='' AND level BETWEEN ? AND ? ORDER BY RANDOM() LIMIT 1", (user_id, max(1,lvl-5), lvl+5))
        row = await cur.fetchone()
        if row: return dict(row)
        cur = await db.execute("SELECT * FROM players WHERE user_id!=? AND class!='' ORDER BY RANDOM() LIMIT 1", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

# ======== БАШНЯ ========
async def get_tower_attempts(user_id):
    from config import TOWER_ATTEMPTS_PER_DAY
    player = await get_player(user_id)
    if not player: return 0
    today = datetime.now().strftime("%Y-%m-%d")
    if player["tower_last_reset"] != today:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE players SET tower_attempts_today=0,tower_last_reset=? WHERE user_id=?", (today, user_id))
            await db.commit()
        return TOWER_ATTEMPTS_PER_DAY
    return max(0, TOWER_ATTEMPTS_PER_DAY - player["tower_attempts_today"])

async def use_tower_attempt(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET tower_attempts_today=tower_attempts_today+1 WHERE user_id=?", (user_id,))
        await db.commit()

async def advance_tower(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET tower_floor=tower_floor+1 WHERE user_id=?", (user_id,))
        await db.commit()

# ======== ИНВЕНТАРЬ ========
async def add_item(user_id, item):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("INSERT INTO inventory (user_id,item_type,name,rarity,bonus_attack,bonus_defense,bonus_hp,bonus_crit) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, item["item_type"], item["name"], item["rarity"], item.get("bonus_attack",0), item.get("bonus_defense",0), item.get("bonus_hp",0), item.get("bonus_crit",0)))
        await db.commit()
        return cur.lastrowid

async def get_inventory(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE user_id=? ORDER BY is_equipped DESC, rarity DESC, id", (user_id,))
        return [dict(r) for r in await cur.fetchall()]

async def get_item(item_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def equip_item(user_id, item_id):
    item = await get_item(item_id)
    if not item or item["user_id"] != user_id: return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE inventory SET is_equipped=0 WHERE user_id=? AND item_type=? AND is_equipped=1", (user_id, item["item_type"]))
        await db.execute("UPDATE inventory SET is_equipped=1 WHERE id=? AND user_id=?", (item_id, user_id))
        await db.commit()

async def sell_item(user_id, item_id):
    from game_data import SELL_PRICES
    item = await get_item(item_id)
    if not item or item["user_id"] != user_id or item["is_equipped"]: return 0
    gold = SELL_PRICES.get(item["rarity"], 30)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        await db.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (gold, user_id))
        await db.commit()
    return gold

async def get_equipment_bonuses(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COALESCE(SUM(bonus_attack),0),COALESCE(SUM(bonus_defense),0),COALESCE(SUM(bonus_hp),0),COALESCE(SUM(bonus_crit),0) FROM inventory WHERE user_id=? AND is_equipped=1", (user_id,))
        r = await cur.fetchone()
        return {"attack": r[0], "defense": r[1], "hp": r[2], "crit": r[3]}

async def get_equipped_items(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE user_id=? AND is_equipped=1", (user_id,))
        return [dict(r) for r in await cur.fetchall()]

async def count_inventory(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM inventory WHERE user_id=?", (user_id,)); return (await cur.fetchone())[0]

async def get_items_by_rarity(user_id, rarity):
    """Получить ненадетые предметы определённой редкости"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE user_id=? AND rarity=? AND is_equipped=0 ORDER BY id", (user_id, rarity))
        return [dict(r) for r in await cur.fetchall()]

async def delete_items(item_ids):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for iid in item_ids:
            await db.execute("DELETE FROM inventory WHERE id=?", (iid,))
        await db.commit()

# ======== КВЕСТЫ ========
async def get_daily_quests(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM quests WHERE user_id=? AND date=?", (user_id, today))
        return [dict(r) for r in await cur.fetchall()]

async def create_daily_quests(user_id, quests):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for q in quests:
            desc = q["desc"].replace("{t}", str(q["target"]))
            await db.execute("INSERT INTO quests (user_id,quest_type,description,target,reward_gold,reward_crystals,reward_xp,date) VALUES (?,?,?,?,?,?,?,?)",
                (user_id, q["type"], desc, q["target"], q["gold"], q["crystals"], q["xp"], today))
        await db.commit()

async def update_quest_progress(user_id, quest_type, amount=1):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""UPDATE quests SET progress=MIN(progress+?,target),
            is_completed=CASE WHEN progress+?>=target THEN 1 ELSE 0 END
            WHERE user_id=? AND quest_type=? AND date=? AND is_claimed=0""",
            (amount, amount, user_id, quest_type, today))
        await db.commit()

async def claim_quest(user_id, quest_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM quests WHERE id=? AND user_id=? AND is_completed=1 AND is_claimed=0", (quest_id, user_id))
        q = await cur.fetchone()
        if not q: return None
        q = dict(q)
        await db.execute("UPDATE quests SET is_claimed=1 WHERE id=?", (quest_id,))
        await db.execute("UPDATE players SET gold=gold+?,crystals=crystals+? WHERE user_id=?", (q["reward_gold"], q["reward_crystals"], user_id))
        await db.commit()
        return q

# ======== ЭКСПЕДИЦИИ ========
async def get_active_expedition(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM expeditions WHERE user_id=? AND is_collected=0 ORDER BY id DESC LIMIT 1", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def start_expedition(user_id, exp_type, duration, rewards):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO expeditions (user_id,exp_type,duration_minutes,started_at,reward_gold,reward_xp,reward_crystals,reward_item_rarity) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, exp_type, duration, now, rewards["gold"], rewards["xp"], rewards["crystals"], rewards.get("item_rarity","")))
        await db.commit()

def is_expedition_done(expedition):
    try:
        started = datetime.fromisoformat(expedition["started_at"])
        return datetime.now() >= started + timedelta(minutes=expedition["duration_minutes"])
    except: return False

def expedition_time_left(expedition):
    try:
        started = datetime.fromisoformat(expedition["started_at"])
        end = started + timedelta(minutes=expedition["duration_minutes"])
        left = end - datetime.now()
        if left.total_seconds() <= 0: return "Готово!"
        mins = int(left.total_seconds() / 60)
        if mins >= 60: return f"{mins//60}ч {mins%60}мин"
        return f"{mins}мин"
    except: return "?"

async def collect_expedition(user_id, exp_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE expeditions SET is_collected=1 WHERE id=? AND user_id=?", (exp_id, user_id))
        await db.commit()

# ======== КОЛЕСО ========
async def can_spin_wheel(user_id):
    player = await get_player(user_id)
    if not player: return False
    return player.get("wheel_last_spin", "") != datetime.now().strftime("%Y-%m-%d")

async def use_wheel_spin(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET wheel_last_spin=? WHERE user_id=?", (today, user_id))
        await db.commit()

# ======== АУКЦИОН ========
async def list_on_auction(seller_id, item_id, price):
    item = await get_item(item_id)
    if not item or item["user_id"] != seller_id or item["is_equipped"]: return False
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO auction (seller_id,item_name,item_type,item_rarity,item_attack,item_defense,item_hp,item_crit,price) VALUES (?,?,?,?,?,?,?,?,?)",
            (seller_id, item["name"], item["item_type"], item["rarity"], item["bonus_attack"], item["bonus_defense"], item["bonus_hp"], item["bonus_crit"], price))
        await db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        await db.commit()
    return True

async def get_auction_listings(limit=20, offset=0):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction ORDER BY listed_at DESC LIMIT ? OFFSET ?", (limit, offset))
        return [dict(r) for r in await cur.fetchall()]

async def get_my_listings(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction WHERE seller_id=?", (user_id,))
        return [dict(r) for r in await cur.fetchall()]

async def count_my_listings(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM auction WHERE seller_id=?", (user_id,))
        return (await cur.fetchone())[0]

async def buy_from_auction(buyer_id, listing_id):
    """Купить предмет с аукциона. Возвращает (успех, инфо)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction WHERE id=?", (listing_id,))
        listing = await cur.fetchone()
        if not listing: return False, "Лот не найден"
        listing = dict(listing)
        if listing["seller_id"] == buyer_id: return False, "Нельзя купить свой лот"
        cur = await db.execute("SELECT gold FROM players WHERE user_id=?", (buyer_id,))
        buyer = await cur.fetchone()
        if not buyer or buyer[0] < listing["price"]: return False, "Не хватает золота"
        # Списать золото у покупателя
        await db.execute("UPDATE players SET gold=gold-? WHERE user_id=?", (listing["price"], buyer_id))
        # Начислить продавцу (минус комиссия)
        seller_gold = int(listing["price"] * 0.9)
        await db.execute("UPDATE players SET gold=gold+? WHERE user_id=?", (seller_gold, listing["seller_id"]))
        # Добавить предмет покупателю
        await db.execute("INSERT INTO inventory (user_id,item_type,name,rarity,bonus_attack,bonus_defense,bonus_hp,bonus_crit) VALUES (?,?,?,?,?,?,?,?)",
            (buyer_id, listing["item_type"], listing["item_name"], listing["item_rarity"], listing["item_attack"], listing["item_defense"], listing["item_hp"], listing["item_crit"]))
        # Удалить лот
        await db.execute("DELETE FROM auction WHERE id=?", (listing_id,))
        await db.commit()
    return True, listing

async def cancel_listing(user_id, listing_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM auction WHERE id=? AND seller_id=?", (listing_id, user_id))
        listing = await cur.fetchone()
        if not listing: return False
        listing = dict(listing)
        # Вернуть предмет
        await db.execute("INSERT INTO inventory (user_id,item_type,name,rarity,bonus_attack,bonus_defense,bonus_hp,bonus_crit) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, listing["item_type"], listing["item_name"], listing["item_rarity"], listing["item_attack"], listing["item_defense"], listing["item_hp"], listing["item_crit"]))
        await db.execute("DELETE FROM auction WHERE id=?", (listing_id,))
        await db.commit()
    return True

async def get_auction_count():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM auction")
        return (await cur.fetchone())[0]

# ======== ЕЖЕДНЕВНЫЙ БОНУС ========
async def check_daily(user_id):
    player = await get_player(user_id)
    if not player: return None
    today = datetime.now().strftime("%Y-%m-%d")
    if player["last_daily"] == today: return None
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    new_streak = player["daily_streak"] + 1 if player["last_daily"] == yesterday else 1
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE players SET last_daily=?,daily_streak=? WHERE user_id=?", (today, new_streak, user_id))
        await db.commit()
    return {"daily_streak": new_streak}

# ======== ЛИДЕРБОРД ========
async def get_leaderboard_xp(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id,username,first_name,class,level,arena_rating,total_kills,tower_floor FROM players WHERE class!='' ORDER BY level DESC,arena_rating DESC LIMIT ?", (limit,))
        return [{"user_id":r[0],"username":r[1],"first_name":r[2],"class":r[3],"level":r[4],"arena_rating":r[5],"total_kills":r[6],"tower_floor":r[7]} for r in await cur.fetchall()]

async def get_leaderboard_arena(limit=10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id,username,first_name,class,level,arena_rating,arena_wins,arena_losses FROM players WHERE class!='' ORDER BY arena_rating DESC LIMIT ?", (limit,))
        return [{"user_id":r[0],"username":r[1],"first_name":r[2],"class":r[3],"level":r[4],"arena_rating":r[5],"arena_wins":r[6],"arena_losses":r[7]} for r in await cur.fetchall()]

async def get_player_rank(user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*)+1 FROM players WHERE class!='' AND (level>(SELECT level FROM players WHERE user_id=?) OR (level=(SELECT level FROM players WHERE user_id=?) AND arena_rating>(SELECT arena_rating FROM players WHERE user_id=?)))", (user_id, user_id, user_id))
        return (await cur.fetchone())[0]

async def get_bot_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        t = (await (await db.execute("SELECT COUNT(*) FROM players WHERE class!=''")).fetchone())[0]
        h = (await (await db.execute("SELECT COALESCE(SUM(total_hunts),0) FROM players")).fetchone())[0]
        a = (await (await db.execute("SELECT COALESCE(SUM(arena_wins+arena_losses),0) FROM players")).fetchone())[0]
        return {"total_players": t, "total_hunts": h, "total_arena_fights": a}
