"""
🗄 База данных текстовой MMO RPG
Игроки, инвентарь, энергия, арена
"""
import aiosqlite
from datetime import datetime
from config import DATABASE_PATH, MAX_ENERGY, ENERGY_REGEN_MINUTES


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                class TEXT DEFAULT '',
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 500,
                crystals INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                max_energy INTEGER DEFAULT 100,
                energy_updated_at TEXT DEFAULT '',
                arena_rating INTEGER DEFAULT 1000,
                arena_wins INTEGER DEFAULT 0,
                arena_losses INTEGER DEFAULT 0,
                arena_fights_today INTEGER DEFAULT 0,
                arena_last_reset TEXT DEFAULT '',
                total_hunts INTEGER DEFAULT 0,
                total_kills INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                last_daily TEXT DEFAULT '',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_type TEXT,
                name TEXT,
                rarity TEXT,
                bonus_attack INTEGER DEFAULT 0,
                bonus_defense INTEGER DEFAULT 0,
                bonus_hp INTEGER DEFAULT 0,
                bonus_crit REAL DEFAULT 0,
                is_equipped INTEGER DEFAULT 0,
                obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()


# ============ ИГРОКИ ============

async def get_player(user_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def create_player(user_id: int, username: str, first_name: str, class_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""
            INSERT OR IGNORE INTO players
            (user_id, username, first_name, class, energy_updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, class_id, now))
        await db.commit()


async def update_player_name(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET username = ?, first_name = ? WHERE user_id = ?",
            (username, first_name, user_id)
        )
        await db.commit()


# ============ ЭНЕРГИЯ ============

def calculate_energy(player: dict) -> int:
    """Рассчитать текущую энергию с учётом регенерации"""
    stored = player["energy"]
    max_e = player["max_energy"]
    if stored >= max_e:
        return max_e

    updated_at = player.get("energy_updated_at", "")
    if not updated_at:
        return stored

    try:
        last = datetime.fromisoformat(updated_at)
        elapsed = (datetime.now() - last).total_seconds() / 60.0
        regen = int(elapsed / ENERGY_REGEN_MINUTES)
        return min(max_e, stored + regen)
    except Exception:
        return stored


async def spend_energy(user_id: int, amount: int, current_energy: int):
    """Потратить энергию"""
    new_energy = current_energy - amount
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET energy = ?, energy_updated_at = ? WHERE user_id = ?",
            (new_energy, now, user_id)
        )
        await db.commit()


async def set_energy(user_id: int, amount: int):
    """Установить энергию"""
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET energy = ?, energy_updated_at = ? WHERE user_id = ?",
            (amount, now, user_id)
        )
        await db.commit()


# ============ РЕСУРСЫ ============

async def add_gold(user_id: int, amount: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET gold = gold + ? WHERE user_id = ?", (amount, user_id)
        )
        await db.commit()


async def add_crystals(user_id: int, amount: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET crystals = crystals + ? WHERE user_id = ?", (amount, user_id)
        )
        await db.commit()


async def spend_gold(user_id: int, amount: int) -> bool:
    """Потратить золото. Вернёт False если не хватает."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT gold FROM players WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount:
            return False
        await db.execute(
            "UPDATE players SET gold = gold - ? WHERE user_id = ?", (amount, user_id)
        )
        await db.commit()
        return True


async def spend_crystals(user_id: int, amount: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT crystals FROM players WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row or row[0] < amount:
            return False
        await db.execute(
            "UPDATE players SET crystals = crystals - ? WHERE user_id = ?", (amount, user_id)
        )
        await db.commit()
        return True


# ============ XP И УРОВЕНЬ ============

async def add_xp(user_id: int, xp: int) -> list:
    """Добавить XP. Возвращает список новых уровней (если были повышения)."""
    from game_data import xp_for_level
    player = await get_player(user_id)
    if not player:
        return []

    current_xp = player["xp"] + xp
    current_level = player["level"]
    new_levels = []

    while current_xp >= xp_for_level(current_level):
        current_xp -= xp_for_level(current_level)
        current_level += 1
        new_levels.append(current_level)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET xp = ?, level = ? WHERE user_id = ?",
            (current_xp, current_level, user_id)
        )
        await db.commit()

    return new_levels


async def record_hunt(user_id: int):
    """Записать охоту"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET total_hunts = total_hunts + 1, total_kills = total_kills + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


# ============ АРЕНА ============

async def get_arena_fights_left(user_id: int) -> int:
    """Сколько боёв арены осталось сегодня"""
    from config import ARENA_FIGHTS_PER_DAY
    player = await get_player(user_id)
    if not player:
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    if player["arena_last_reset"] != today:
        # Новый день — сброс
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE players SET arena_fights_today = 0, arena_last_reset = ? WHERE user_id = ?",
                (today, user_id)
            )
            await db.commit()
        return ARENA_FIGHTS_PER_DAY

    return max(0, ARENA_FIGHTS_PER_DAY - player["arena_fights_today"])


async def record_arena_fight(user_id: int, won: bool, rating_change: int):
    """Записать бой арены"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if won:
            await db.execute("""
                UPDATE players SET
                    arena_wins = arena_wins + 1,
                    arena_fights_today = arena_fights_today + 1,
                    arena_rating = MAX(0, arena_rating + ?)
                WHERE user_id = ?
            """, (rating_change, user_id))
        else:
            await db.execute("""
                UPDATE players SET
                    arena_losses = arena_losses + 1,
                    arena_fights_today = arena_fights_today + 1,
                    arena_rating = MAX(0, arena_rating + ?)
                WHERE user_id = ?
            """, (-abs(rating_change), user_id))
        await db.commit()


async def get_arena_opponent(user_id: int) -> dict | None:
    """Найти противника для арены (±5 уровней)"""
    player = await get_player(user_id)
    if not player:
        return None

    lvl = player["level"]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT * FROM players
            WHERE user_id != ? AND class != '' AND level BETWEEN ? AND ?
            ORDER BY RANDOM() LIMIT 1
        """, (user_id, max(1, lvl - 5), lvl + 5))
        row = await cur.fetchone()
        if row:
            return dict(row)

        # Если нет — берём любого
        cur = await db.execute("""
            SELECT * FROM players
            WHERE user_id != ? AND class != ''
            ORDER BY RANDOM() LIMIT 1
        """, (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


# ============ ИНВЕНТАРЬ ============

async def add_item(user_id: int, item: dict) -> int:
    """Добавить предмет в инвентарь. Вернёт ID предмета."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""
            INSERT INTO inventory (user_id, item_type, name, rarity,
                bonus_attack, bonus_defense, bonus_hp, bonus_crit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, item["item_type"], item["name"], item["rarity"],
            item.get("bonus_attack", 0), item.get("bonus_defense", 0),
            item.get("bonus_hp", 0), item.get("bonus_crit", 0),
        ))
        await db.commit()
        return cur.lastrowid


async def get_inventory(user_id: int) -> list:
    """Получить инвентарь игрока"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM inventory WHERE user_id = ? ORDER BY is_equipped DESC, rarity DESC, id",
            (user_id,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_item(item_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def equip_item(user_id: int, item_id: int):
    """Надеть предмет (снять старый того же типа)"""
    item = await get_item(item_id)
    if not item or item["user_id"] != user_id:
        return

    # Снимаем текущий предмет того же типа
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE inventory SET is_equipped = 0
            WHERE user_id = ? AND item_type = ? AND is_equipped = 1
        """, (user_id, item["item_type"]))

        # Надеваем новый
        await db.execute(
            "UPDATE inventory SET is_equipped = 1 WHERE id = ? AND user_id = ?",
            (item_id, user_id)
        )
        await db.commit()


async def sell_item(user_id: int, item_id: int) -> int:
    """Продать предмет. Вернёт золото (0 если ошибка)."""
    from game_data import SELL_PRICES
    item = await get_item(item_id)
    if not item or item["user_id"] != user_id or item["is_equipped"]:
        return 0

    gold = SELL_PRICES.get(item["rarity"], 30)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        await db.execute(
            "UPDATE players SET gold = gold + ? WHERE user_id = ?", (gold, user_id)
        )
        await db.commit()

    return gold


async def get_equipment_bonuses(user_id: int) -> dict:
    """Получить суммарные бонусы от экипировки"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""
            SELECT
                COALESCE(SUM(bonus_attack), 0) as attack,
                COALESCE(SUM(bonus_defense), 0) as defense,
                COALESCE(SUM(bonus_hp), 0) as hp,
                COALESCE(SUM(bonus_crit), 0) as crit
            FROM inventory
            WHERE user_id = ? AND is_equipped = 1
        """, (user_id,))
        row = await cur.fetchone()
        return {"attack": row[0], "defense": row[1], "hp": row[2], "crit": row[3]}


async def get_equipped_items(user_id: int) -> list:
    """Получить надетые предметы"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM inventory WHERE user_id = ? AND is_equipped = 1",
            (user_id,)
        )
        return [dict(r) for r in await cur.fetchall()]


async def count_inventory(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM inventory WHERE user_id = ?", (user_id,)
        )
        return (await cur.fetchone())[0]


# ============ ЕЖЕДНЕВНЫЙ БОНУС ============

async def check_daily(user_id: int) -> dict | None:
    """Проверить ежедневный бонус. None = уже получен."""
    from datetime import timedelta
    player = await get_player(user_id)
    if not player:
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    if player["last_daily"] == today:
        return None

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    new_streak = player["daily_streak"] + 1 if player["last_daily"] == yesterday else 1

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE players SET last_daily = ?, daily_streak = ? WHERE user_id = ?",
            (today, new_streak, user_id)
        )
        await db.commit()

    return {"daily_streak": new_streak}


# ============ ЛИДЕРБОРД ============

async def get_leaderboard_xp(limit: int = 10) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""
            SELECT user_id, username, first_name, class, level, gold + crystals * 100 as power,
                   arena_rating, arena_wins, total_kills
            FROM players WHERE class != ''
            ORDER BY level DESC, arena_rating DESC
            LIMIT ?
        """, (limit,))
        rows = await cur.fetchall()
        return [
            {"user_id": r[0], "username": r[1], "first_name": r[2], "class": r[3],
             "level": r[4], "power": r[5], "arena_rating": r[6], "arena_wins": r[7],
             "total_kills": r[8]}
            for r in rows
        ]


async def get_leaderboard_arena(limit: int = 10) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""
            SELECT user_id, username, first_name, class, level, arena_rating, arena_wins, arena_losses
            FROM players WHERE class != ''
            ORDER BY arena_rating DESC
            LIMIT ?
        """, (limit,))
        rows = await cur.fetchall()
        return [
            {"user_id": r[0], "username": r[1], "first_name": r[2], "class": r[3],
             "level": r[4], "arena_rating": r[5], "arena_wins": r[6], "arena_losses": r[7]}
            for r in rows
        ]


async def get_player_rank(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("""
            SELECT COUNT(*) + 1 FROM players
            WHERE class != '' AND (level > (SELECT level FROM players WHERE user_id = ?)
                OR (level = (SELECT level FROM players WHERE user_id = ?)
                    AND arena_rating > (SELECT arena_rating FROM players WHERE user_id = ?)))
        """, (user_id, user_id, user_id))
        return (await cur.fetchone())[0]


# ============ СТАТИСТИКА ============

async def get_bot_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM players WHERE class != ''")
        total = (await cur.fetchone())[0]
        cur = await db.execute("SELECT SUM(total_hunts) FROM players")
        hunts = (await cur.fetchone())[0] or 0
        cur = await db.execute("SELECT SUM(arena_wins + arena_losses) FROM players")
        arena = (await cur.fetchone())[0] or 0
        return {"total_players": total, "total_hunts": hunts, "total_arena_fights": arena}
