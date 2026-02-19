"""
⚔️ Данные игрового мира — текстовая MMO RPG
Классы, монстры, зоны, предметы, гача, боевая система
"""
import random
import math

# ============ РЕДКОСТЬ ============
RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]

RARITY_EMOJI = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟡",
}

RARITY_NAMES = {
    "common": "Обычный",
    "uncommon": "Необычный",
    "rare": "Редкий",
    "epic": "Эпический",
    "legendary": "Легендарный",
}

SELL_PRICES = {
    "common": 30,
    "uncommon": 80,
    "rare": 250,
    "epic": 800,
    "legendary": 3000,
}

# ============ КЛАССЫ ============
CLASSES = {
    "warrior": {
        "name": "⚔️ Воин",
        "desc": "Крепкий боец ближнего боя. Много HP и хорошая защита.",
        "base_hp": 130,
        "base_attack": 12,
        "base_defense": 8,
        "base_crit": 5.0,
        "hp_per_lvl": 7,
        "atk_per_lvl": 2.0,
        "def_per_lvl": 1.5,
    },
    "mage": {
        "name": "🧙 Маг",
        "desc": "Мощные заклинания, но хрупкий. Высокий урон и крит.",
        "base_hp": 80,
        "base_attack": 18,
        "base_defense": 4,
        "base_crit": 12.0,
        "hp_per_lvl": 3,
        "atk_per_lvl": 3.0,
        "def_per_lvl": 0.5,
    },
    "assassin": {
        "name": "🗡 Ассасин",
        "desc": "Быстрый и смертоносный. Огромный шанс критического удара.",
        "base_hp": 95,
        "base_attack": 15,
        "base_defense": 5,
        "base_crit": 20.0,
        "hp_per_lvl": 4,
        "atk_per_lvl": 2.5,
        "def_per_lvl": 1.0,
    },
    "paladin": {
        "name": "🛡 Паладин",
        "desc": "Несокрушимый защитник. Максимум HP и брони.",
        "base_hp": 160,
        "base_attack": 10,
        "base_defense": 10,
        "base_crit": 3.0,
        "hp_per_lvl": 9,
        "atk_per_lvl": 1.5,
        "def_per_lvl": 2.0,
    },
}


def get_class_stats(class_id: str, level: int) -> dict:
    """Получить базовые статы класса для уровня"""
    c = CLASSES[class_id]
    return {
        "max_hp": int(c["base_hp"] + (level - 1) * c["hp_per_lvl"]),
        "attack": int(c["base_attack"] + (level - 1) * c["atk_per_lvl"]),
        "defense": int(c["base_defense"] + (level - 1) * c["def_per_lvl"]),
        "crit": c["base_crit"],
    }


def xp_for_level(level: int) -> int:
    """XP для перехода на следующий уровень"""
    return 100 + (level - 1) * 50


# ============ ЗОНЫ И МОНСТРЫ ============
ZONES = [
    {
        "id": 1,
        "name": "🌿 Зелёные поля",
        "min_level": 1,
        "monsters": [
            {"name": "Слайм", "emoji": "🟢", "hp": 35, "attack": 5, "defense": 2, "xp": 18, "gold": 15},
            {"name": "Гоблин", "emoji": "👺", "hp": 45, "attack": 8, "defense": 3, "xp": 22, "gold": 20},
            {"name": "Дикий волк", "emoji": "🐺", "hp": 55, "attack": 10, "defense": 4, "xp": 28, "gold": 22},
            {"name": "Бандит", "emoji": "🥷", "hp": 65, "attack": 12, "defense": 5, "xp": 32, "gold": 28},
            {"name": "Гигантский паук", "emoji": "🕷", "hp": 50, "attack": 14, "defense": 3, "xp": 35, "gold": 30},
        ],
        "drop_chance": 15,
        "drop_rates": {"common": 70, "uncommon": 25, "rare": 5},
    },
    {
        "id": 2,
        "name": "🌲 Тёмный лес",
        "min_level": 10,
        "monsters": [
            {"name": "Орк", "emoji": "👹", "hp": 120, "attack": 22, "defense": 10, "xp": 55, "gold": 50},
            {"name": "Скелет-воин", "emoji": "💀", "hp": 100, "attack": 25, "defense": 8, "xp": 50, "gold": 45},
            {"name": "Тёмный маг", "emoji": "🧙‍♂️", "hp": 85, "attack": 30, "defense": 6, "xp": 62, "gold": 55},
            {"name": "Минотавр", "emoji": "🐂", "hp": 150, "attack": 20, "defense": 14, "xp": 65, "gold": 60},
            {"name": "Тролль", "emoji": "🧌", "hp": 180, "attack": 18, "defense": 16, "xp": 70, "gold": 65},
        ],
        "drop_chance": 18,
        "drop_rates": {"common": 20, "uncommon": 50, "rare": 25, "epic": 5},
    },
    {
        "id": 3,
        "name": "🏚 Проклятые руины",
        "min_level": 22,
        "monsters": [
            {"name": "Вампир", "emoji": "🧛", "hp": 220, "attack": 40, "defense": 18, "xp": 110, "gold": 100},
            {"name": "Некромант", "emoji": "☠️", "hp": 190, "attack": 48, "defense": 14, "xp": 120, "gold": 110},
            {"name": "Горгулья", "emoji": "🗿", "hp": 280, "attack": 35, "defense": 28, "xp": 125, "gold": 105},
            {"name": "Элементаль", "emoji": "🔥", "hp": 200, "attack": 55, "defense": 12, "xp": 135, "gold": 120},
            {"name": "Страж руин", "emoji": "⚔️", "hp": 300, "attack": 42, "defense": 25, "xp": 145, "gold": 130},
        ],
        "drop_chance": 20,
        "drop_rates": {"uncommon": 15, "rare": 50, "epic": 30, "legendary": 5},
    },
    {
        "id": 4,
        "name": "🐉 Логово дракона",
        "min_level": 35,
        "monsters": [
            {"name": "Чёрный рыцарь", "emoji": "🖤", "hp": 400, "attack": 65, "defense": 35, "xp": 200, "gold": 200},
            {"name": "Демон", "emoji": "😈", "hp": 350, "attack": 80, "defense": 25, "xp": 220, "gold": 220},
            {"name": "Древний голем", "emoji": "🪨", "hp": 550, "attack": 50, "defense": 50, "xp": 240, "gold": 210},
            {"name": "Дракон", "emoji": "🐉", "hp": 500, "attack": 75, "defense": 40, "xp": 280, "gold": 260},
            {"name": "Хранитель портала", "emoji": "🌀", "hp": 450, "attack": 90, "defense": 30, "xp": 300, "gold": 280},
        ],
        "drop_chance": 25,
        "drop_rates": {"rare": 20, "epic": 50, "legendary": 30},
    },
]


def get_available_zones(level: int) -> list:
    """Получить доступные зоны для уровня"""
    return [z for z in ZONES if level >= z["min_level"]]


def pick_monster(zone_id: int) -> dict:
    """Выбрать случайного монстра из зоны"""
    zone = next(z for z in ZONES if z["id"] == zone_id)
    return random.choice(zone["monsters"])


# ============ ПРЕДМЕТЫ ============
WEAPONS = {
    "common": [
        {"name": "Деревянный меч", "attack": 3, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Ржавый кинжал", "attack": 2, "defense": 0, "hp": 0, "crit": 1.0},
        {"name": "Каменный топор", "attack": 4, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Старая палка", "attack": 2, "defense": 1, "hp": 0, "crit": 0},
    ],
    "uncommon": [
        {"name": "Стальной меч", "attack": 6, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Охотничий кинжал", "attack": 5, "defense": 0, "hp": 0, "crit": 2.0},
        {"name": "Железный топор", "attack": 7, "defense": 0, "hp": 0, "crit": 0},
        {"name": "Боевой молот", "attack": 6, "defense": 1, "hp": 5, "crit": 0},
    ],
    "rare": [
        {"name": "Зачарованный клинок", "attack": 10, "defense": 0, "hp": 0, "crit": 2.0},
        {"name": "Клинок ветра", "attack": 9, "defense": 0, "hp": 0, "crit": 3.0},
        {"name": "Магический жезл", "attack": 12, "defense": 0, "hp": 0, "crit": 1.0},
        {"name": "Серебряный меч", "attack": 11, "defense": 2, "hp": 0, "crit": 0},
    ],
    "epic": [
        {"name": "Драконий клинок", "attack": 17, "defense": 0, "hp": 10, "crit": 3.0},
        {"name": "Теневой кинжал", "attack": 14, "defense": 0, "hp": 0, "crit": 6.0},
        {"name": "Посох Бездны", "attack": 20, "defense": 0, "hp": 0, "crit": 2.0},
        {"name": "Молот Грома", "attack": 16, "defense": 3, "hp": 15, "crit": 0},
    ],
    "legendary": [
        {"name": "🔥 Экскалибур", "attack": 30, "defense": 5, "hp": 20, "crit": 5.0},
        {"name": "⚡ Мьёльнир", "attack": 28, "defense": 8, "hp": 30, "crit": 3.0},
        {"name": "💀 Жнец Душ", "attack": 35, "defense": 0, "hp": 0, "crit": 8.0},
        {"name": "✨ Клинок Бога", "attack": 32, "defense": 3, "hp": 10, "crit": 6.0},
    ],
}

ARMORS = {
    "common": [
        {"name": "Тряпичная рубашка", "attack": 0, "defense": 2, "hp": 8, "crit": 0},
        {"name": "Кожаный жилет", "attack": 0, "defense": 3, "hp": 5, "crit": 0},
        {"name": "Деревянный щит", "attack": 0, "defense": 3, "hp": 10, "crit": 0},
    ],
    "uncommon": [
        {"name": "Кольчуга", "attack": 0, "defense": 5, "hp": 15, "crit": 0},
        {"name": "Кожаная броня", "attack": 0, "defense": 4, "hp": 20, "crit": 0},
        {"name": "Железный щит", "attack": 0, "defense": 6, "hp": 12, "crit": 0},
    ],
    "rare": [
        {"name": "Латные доспехи", "attack": 0, "defense": 8, "hp": 30, "crit": 0},
        {"name": "Мифриловая кольчуга", "attack": 1, "defense": 7, "hp": 25, "crit": 0},
        {"name": "Магический плащ", "attack": 2, "defense": 6, "hp": 20, "crit": 1.0},
    ],
    "epic": [
        {"name": "Доспехи Дракона", "attack": 2, "defense": 14, "hp": 50, "crit": 0},
        {"name": "Теневая мантия", "attack": 3, "defense": 10, "hp": 30, "crit": 3.0},
        {"name": "Щит Титана", "attack": 0, "defense": 16, "hp": 60, "crit": 0},
    ],
    "legendary": [
        {"name": "🔥 Доспехи Бога", "attack": 5, "defense": 22, "hp": 80, "crit": 2.0},
        {"name": "⚡ Одеяние Архимага", "attack": 8, "defense": 15, "hp": 50, "crit": 5.0},
        {"name": "💀 Броня Бессмертного", "attack": 0, "defense": 25, "hp": 100, "crit": 0},
    ],
}

ACCESSORIES = {
    "common": [
        {"name": "Медное кольцо", "attack": 1, "defense": 1, "hp": 3, "crit": 0},
        {"name": "Кожаный браслет", "attack": 2, "defense": 0, "hp": 5, "crit": 0},
        {"name": "Деревянный амулет", "attack": 0, "defense": 1, "hp": 8, "crit": 0.5},
    ],
    "uncommon": [
        {"name": "Серебряное кольцо", "attack": 2, "defense": 2, "hp": 8, "crit": 1.0},
        {"name": "Амулет удачи", "attack": 1, "defense": 1, "hp": 5, "crit": 2.0},
        {"name": "Браслет силы", "attack": 4, "defense": 0, "hp": 10, "crit": 0},
    ],
    "rare": [
        {"name": "Кольцо мощи", "attack": 5, "defense": 3, "hp": 15, "crit": 1.0},
        {"name": "Амулет крови", "attack": 3, "defense": 2, "hp": 25, "crit": 2.0},
        {"name": "Браслет теней", "attack": 4, "defense": 1, "hp": 10, "crit": 4.0},
    ],
    "epic": [
        {"name": "Кольцо Дракона", "attack": 8, "defense": 5, "hp": 25, "crit": 3.0},
        {"name": "Амулет Бездны", "attack": 10, "defense": 3, "hp": 15, "crit": 4.0},
        {"name": "Печать Короля", "attack": 6, "defense": 6, "hp": 30, "crit": 2.0},
    ],
    "legendary": [
        {"name": "🔥 Перстень Всевластия", "attack": 15, "defense": 8, "hp": 40, "crit": 5.0},
        {"name": "⚡ Амулет Вечности", "attack": 10, "defense": 10, "hp": 60, "crit": 3.0},
        {"name": "💀 Ожерелье Смерти", "attack": 18, "defense": 3, "hp": 20, "crit": 8.0},
    ],
}

# ============ ГАЧА ============
GACHA_FREE_COST = 500       # Золото
GACHA_PREM_COST = 50        # Кристаллы
GACHA_10X_COST = 450        # Кристаллы (скидка)

GACHA_RATES_FREE = {"common": 50, "uncommon": 30, "rare": 15, "epic": 4, "legendary": 1}
GACHA_RATES_PREMIUM = {"uncommon": 30, "rare": 40, "epic": 25, "legendary": 5}


def _pick_rarity(rates: dict) -> str:
    """Выбрать редкость по таблице вероятностей"""
    roll = random.randint(1, 100)
    cumulative = 0
    for rarity, chance in rates.items():
        cumulative += chance
        if roll <= cumulative:
            return rarity
    return list(rates.keys())[-1]


def generate_item(rarity: str, item_type: str = None) -> dict:
    """Сгенерировать предмет заданной редкости"""
    if not item_type:
        item_type = random.choice(["weapon", "armor", "accessory"])

    templates = {"weapon": WEAPONS, "armor": ARMORS, "accessory": ACCESSORIES}
    pool = templates[item_type].get(rarity, templates[item_type]["common"])
    base = random.choice(pool)

    # Небольшой рандом ±15%
    def vary(val):
        if val == 0:
            return 0
        return max(1, int(val * random.uniform(0.85, 1.15)))

    return {
        "item_type": item_type,
        "name": base["name"],
        "rarity": rarity,
        "bonus_attack": vary(base["attack"]),
        "bonus_defense": vary(base["defense"]),
        "bonus_hp": vary(base["hp"]),
        "bonus_crit": round(base["crit"] * random.uniform(0.9, 1.1), 1),
    }


def gacha_pull(is_premium: bool = False) -> dict:
    """Один гача-ролл"""
    rates = GACHA_RATES_PREMIUM if is_premium else GACHA_RATES_FREE
    rarity = _pick_rarity(rates)
    return generate_item(rarity)


def gacha_pull_10x() -> list:
    """10 гача-роллов (премиум), гарантия 1 epic+"""
    items = [gacha_pull(is_premium=True) for _ in range(10)]
    # Гарантия — хотя бы 1 epic+
    has_epic = any(i["rarity"] in ("epic", "legendary") for i in items)
    if not has_epic:
        items[-1] = generate_item(random.choice(["epic", "legendary"]))
    return items


# ============ БОЕВАЯ СИСТЕМА ============

def simulate_combat(attacker: dict, defender: dict) -> dict:
    """
    Симуляция боя.
    attacker/defender = {"hp": int, "attack": int, "defense": int, "crit": float}
    Возвращает результат боя.
    """
    atk_hp = attacker["hp"]
    def_hp = defender["hp"]
    rounds_log = []
    total_dmg_dealt = 0
    total_dmg_received = 0
    crits = 0
    rounds = 0

    while atk_hp > 0 and def_hp > 0 and rounds < 25:
        rounds += 1

        # Атакующий бьёт
        is_crit = random.random() * 100 < attacker["crit"]
        raw_dmg = attacker["attack"] * random.uniform(0.8, 1.2)
        dmg = max(1, raw_dmg - defender["defense"] * 0.3)
        if is_crit:
            dmg *= 2
            crits += 1
        dmg = int(dmg)
        def_hp -= dmg
        total_dmg_dealt += dmg

        crit_text = " 💥КРИТ!" if is_crit else ""
        rounds_log.append(f"⚔️ Ты: -{dmg} HP{crit_text}")

        if def_hp <= 0:
            break

        # Защитник бьёт
        raw_dmg = defender["attack"] * random.uniform(0.8, 1.2)
        dmg_back = max(1, raw_dmg - attacker["defense"] * 0.3)
        dmg_back = int(dmg_back)
        atk_hp -= dmg_back
        total_dmg_received += dmg_back
        rounds_log.append(f"👹 Враг: -{dmg_back} HP")

    won = def_hp <= 0
    return {
        "won": won,
        "rounds": rounds,
        "log": rounds_log[:10],  # Макс 10 строк лога
        "damage_dealt": total_dmg_dealt,
        "damage_received": total_dmg_received,
        "crits": crits,
        "hp_left": max(0, atk_hp),
        "hp_max": attacker["hp"],
    }


def get_total_stats(base_stats: dict, equipment_bonuses: dict) -> dict:
    """Суммарные статы = база + экипировка"""
    return {
        "hp": base_stats["max_hp"] + equipment_bonuses.get("hp", 0),
        "attack": base_stats["attack"] + equipment_bonuses.get("attack", 0),
        "defense": base_stats["defense"] + equipment_bonuses.get("defense", 0),
        "crit": base_stats["crit"] + equipment_bonuses.get("crit", 0),
    }


# ============ ВСПОМОГАТЕЛЬНЫЕ ============
TYPE_EMOJI = {"weapon": "🗡", "armor": "🛡", "accessory": "💍"}
TYPE_NAMES = {"weapon": "Оружие", "armor": "Броня", "accessory": "Аксессуар"}


def hp_bar(current: int, maximum: int, length: int = 10) -> str:
    """Полоска HP"""
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    filled = int(ratio * length)
    return "█" * filled + "░" * (length - filled)


def format_item_short(item: dict) -> str:
    """Короткое описание предмета"""
    emoji = TYPE_EMOJI.get(item.get("item_type", ""), "📦")
    rarity_e = RARITY_EMOJI.get(item.get("rarity", "common"), "⚪")
    name = item.get("name", "???")
    return f"{emoji} {rarity_e} {name}"


def format_item_stats(item: dict) -> str:
    """Статы предмета"""
    parts = []
    if item.get("bonus_attack", 0) > 0:
        parts.append(f"+{item['bonus_attack']} ATK")
    if item.get("bonus_defense", 0) > 0:
        parts.append(f"+{item['bonus_defense']} DEF")
    if item.get("bonus_hp", 0) > 0:
        parts.append(f"+{item['bonus_hp']} HP")
    if item.get("bonus_crit", 0) > 0:
        parts.append(f"+{item['bonus_crit']}% КРИТ")
    return ", ".join(parts) if parts else "—"


def try_drop_item(zone_id: int) -> dict | None:
    """Попытка дропа предмета из зоны"""
    zone = next((z for z in ZONES if z["id"] == zone_id), None)
    if not zone:
        return None
    if random.randint(1, 100) > zone["drop_chance"]:
        return None
    rarity = _pick_rarity(zone["drop_rates"])
    return generate_item(rarity)
