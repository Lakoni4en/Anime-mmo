"""
⚔️ Данные игрового мира — текстовая MMO RPG v2
Классы, монстры, 8 зон, башня, квесты, экспедиции, колесо, крафт, аукцион
"""
import random

# ============ РЕДКОСТЬ ============
RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
RARITY_EMOJI = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}
RARITY_NAMES = {"common": "Обычный", "uncommon": "Необычный", "rare": "Редкий", "epic": "Эпический", "legendary": "Легендарный"}
SELL_PRICES = {"common": 30, "uncommon": 80, "rare": 250, "epic": 800, "legendary": 3000}

# Цены аукциона (множители к SELL_PRICES)
AUCTION_PRICE_TIERS = {1: 2, 2: 3, 3: 5}
AUCTION_FEE = 0.10  # 10% комиссия

# Крафт — стоимость улучшения
UPGRADE_COSTS = {"common": 100, "uncommon": 300, "rare": 1000, "epic": 5000}
UPGRADE_NEXT = {"common": "uncommon", "uncommon": "rare", "rare": "epic", "epic": "legendary"}

# ============ КЛАССЫ ============
CLASSES = {
    "warrior": {
        "name": "⚔️ Воин", "desc": "Крепкий боец. Много HP и хорошая защита.",
        "base_hp": 130, "base_attack": 12, "base_defense": 8, "base_crit": 5.0,
        "hp_per_lvl": 7, "atk_per_lvl": 2.0, "def_per_lvl": 1.5,
    },
    "mage": {
        "name": "🧙 Маг", "desc": "Стеклянная пушка. Огромный урон и крит.",
        "base_hp": 80, "base_attack": 18, "base_defense": 4, "base_crit": 12.0,
        "hp_per_lvl": 3, "atk_per_lvl": 3.0, "def_per_lvl": 0.5,
    },
    "assassin": {
        "name": "🗡 Ассасин", "desc": "Быстрый и смертоносный. Критует как бог.",
        "base_hp": 95, "base_attack": 15, "base_defense": 5, "base_crit": 20.0,
        "hp_per_lvl": 4, "atk_per_lvl": 2.5, "def_per_lvl": 1.0,
    },
    "paladin": {
        "name": "🛡 Паладин", "desc": "Несокрушимый защитник. Максимум HP и брони.",
        "base_hp": 160, "base_attack": 10, "base_defense": 10, "base_crit": 3.0,
        "hp_per_lvl": 9, "atk_per_lvl": 1.5, "def_per_lvl": 2.0,
    },
}


def get_class_stats(class_id: str, level: int) -> dict:
    c = CLASSES[class_id]
    return {
        "max_hp": int(c["base_hp"] + (level - 1) * c["hp_per_lvl"]),
        "attack": int(c["base_attack"] + (level - 1) * c["atk_per_lvl"]),
        "defense": int(c["base_defense"] + (level - 1) * c["def_per_lvl"]),
        "crit": c["base_crit"],
    }


def xp_for_level(level: int) -> int:
    return 100 + (level - 1) * 50


# ============ 8 ЗОН С МОНСТРАМИ ============
ZONES = [
    {
        "id": 1, "name": "🌿 Зелёные поля", "min_level": 1,
        "monsters": [
            {"name": "Слайм", "emoji": "🟢", "hp": 35, "attack": 5, "defense": 2, "xp": 18, "gold": 15},
            {"name": "Гоблин", "emoji": "👺", "hp": 45, "attack": 8, "defense": 3, "xp": 22, "gold": 20},
            {"name": "Дикий волк", "emoji": "🐺", "hp": 55, "attack": 10, "defense": 4, "xp": 28, "gold": 22},
            {"name": "Бандит", "emoji": "🥷", "hp": 65, "attack": 12, "defense": 5, "xp": 32, "gold": 28},
            {"name": "Гигантский паук", "emoji": "🕷", "hp": 50, "attack": 14, "defense": 3, "xp": 35, "gold": 30},
        ],
        "boss": {"name": "🔴 Король гоблинов", "hp": 150, "attack": 20, "defense": 10, "xp": 100, "gold": 120},
        "drop_chance": 15, "drop_rates": {"common": 70, "uncommon": 25, "rare": 5},
    },
    {
        "id": 2, "name": "🌲 Тёмный лес", "min_level": 10,
        "monsters": [
            {"name": "Орк", "emoji": "👹", "hp": 120, "attack": 22, "defense": 10, "xp": 55, "gold": 50},
            {"name": "Скелет-воин", "emoji": "💀", "hp": 100, "attack": 25, "defense": 8, "xp": 50, "gold": 45},
            {"name": "Тёмный маг", "emoji": "🧙‍♂️", "hp": 85, "attack": 30, "defense": 6, "xp": 62, "gold": 55},
            {"name": "Минотавр", "emoji": "🐂", "hp": 150, "attack": 20, "defense": 14, "xp": 65, "gold": 60},
            {"name": "Тролль", "emoji": "🧌", "hp": 180, "attack": 18, "defense": 16, "xp": 70, "gold": 65},
        ],
        "boss": {"name": "🔴 Лесной дух", "hp": 300, "attack": 40, "defense": 20, "xp": 200, "gold": 250},
        "drop_chance": 18, "drop_rates": {"common": 20, "uncommon": 50, "rare": 25, "epic": 5},
    },
    {
        "id": 3, "name": "🏚 Проклятые руины", "min_level": 22,
        "monsters": [
            {"name": "Вампир", "emoji": "🧛", "hp": 220, "attack": 40, "defense": 18, "xp": 110, "gold": 100},
            {"name": "Некромант", "emoji": "☠️", "hp": 190, "attack": 48, "defense": 14, "xp": 120, "gold": 110},
            {"name": "Горгулья", "emoji": "🗿", "hp": 280, "attack": 35, "defense": 28, "xp": 125, "gold": 105},
            {"name": "Элементаль", "emoji": "🔥", "hp": 200, "attack": 55, "defense": 12, "xp": 135, "gold": 120},
            {"name": "Страж руин", "emoji": "⚔️", "hp": 300, "attack": 42, "defense": 25, "xp": 145, "gold": 130},
        ],
        "boss": {"name": "🔴 Лич-повелитель", "hp": 500, "attack": 65, "defense": 30, "xp": 400, "gold": 450},
        "drop_chance": 20, "drop_rates": {"uncommon": 15, "rare": 50, "epic": 30, "legendary": 5},
    },
    {
        "id": 4, "name": "🐉 Логово дракона", "min_level": 35,
        "monsters": [
            {"name": "Чёрный рыцарь", "emoji": "🖤", "hp": 400, "attack": 65, "defense": 35, "xp": 200, "gold": 200},
            {"name": "Демон", "emoji": "😈", "hp": 350, "attack": 80, "defense": 25, "xp": 220, "gold": 220},
            {"name": "Древний голем", "emoji": "🪨", "hp": 550, "attack": 50, "defense": 50, "xp": 240, "gold": 210},
            {"name": "Дракон", "emoji": "🐉", "hp": 500, "attack": 75, "defense": 40, "xp": 280, "gold": 260},
            {"name": "Хранитель портала", "emoji": "🌀", "hp": 450, "attack": 90, "defense": 30, "xp": 300, "gold": 280},
        ],
        "boss": {"name": "🔴 Древний дракон", "hp": 900, "attack": 100, "defense": 50, "xp": 700, "gold": 700},
        "drop_chance": 25, "drop_rates": {"rare": 20, "epic": 50, "legendary": 30},
    },
    {
        "id": 5, "name": "☁️ Небесная крепость", "min_level": 50,
        "monsters": [
            {"name": "Ангел-страж", "emoji": "👼", "hp": 650, "attack": 110, "defense": 50, "xp": 420, "gold": 380},
            {"name": "Грифон", "emoji": "🦅", "hp": 700, "attack": 100, "defense": 55, "xp": 450, "gold": 400},
            {"name": "Небесный голем", "emoji": "🏛", "hp": 900, "attack": 90, "defense": 70, "xp": 480, "gold": 420},
            {"name": "Архангел", "emoji": "✨", "hp": 600, "attack": 130, "defense": 45, "xp": 500, "gold": 450},
            {"name": "Серафим", "emoji": "🌟", "hp": 750, "attack": 120, "defense": 60, "xp": 550, "gold": 480},
        ],
        "boss": {"name": "🔴 Падший серафим", "hp": 1500, "attack": 160, "defense": 70, "xp": 1200, "gold": 1100},
        "drop_chance": 28, "drop_rates": {"rare": 30, "epic": 50, "legendary": 20},
    },
    {
        "id": 6, "name": "🌋 Вулкан Хаоса", "min_level": 65,
        "monsters": [
            {"name": "Лавовый элементаль", "emoji": "🔥", "hp": 950, "attack": 150, "defense": 65, "xp": 650, "gold": 550},
            {"name": "Огненный дракон", "emoji": "🐲", "hp": 1100, "attack": 140, "defense": 70, "xp": 700, "gold": 600},
            {"name": "Демон Хаоса", "emoji": "👿", "hp": 900, "attack": 170, "defense": 55, "xp": 720, "gold": 620},
            {"name": "Инфернал", "emoji": "💀", "hp": 1000, "attack": 160, "defense": 75, "xp": 750, "gold": 650},
            {"name": "Повелитель пепла", "emoji": "🌑", "hp": 1300, "attack": 145, "defense": 85, "xp": 800, "gold": 700},
        ],
        "boss": {"name": "🔴 Ифрит", "hp": 2500, "attack": 220, "defense": 90, "xp": 2000, "gold": 1800},
        "drop_chance": 30, "drop_rates": {"rare": 10, "epic": 55, "legendary": 35},
    },
    {
        "id": 7, "name": "❄️ Ледяная пустошь", "min_level": 80,
        "monsters": [
            {"name": "Ледяной великан", "emoji": "🧊", "hp": 1400, "attack": 190, "defense": 90, "xp": 950, "gold": 850},
            {"name": "Фростворм", "emoji": "🐍", "hp": 1200, "attack": 220, "defense": 80, "xp": 1000, "gold": 900},
            {"name": "Снежная ведьма", "emoji": "🧙‍♀️", "hp": 1100, "attack": 240, "defense": 70, "xp": 1050, "gold": 950},
            {"name": "Ледяной феникс", "emoji": "🦢", "hp": 1500, "attack": 200, "defense": 100, "xp": 1100, "gold": 1000},
            {"name": "Криоголем", "emoji": "🗻", "hp": 1800, "attack": 180, "defense": 120, "xp": 1200, "gold": 1050},
        ],
        "boss": {"name": "🔴 Король вечной зимы", "hp": 3500, "attack": 300, "defense": 120, "xp": 3000, "gold": 2800},
        "drop_chance": 33, "drop_rates": {"epic": 50, "legendary": 50},
    },
    {
        "id": 8, "name": "🕳 Бездна", "min_level": 100,
        "monsters": [
            {"name": "Порождение Бездны", "emoji": "👁", "hp": 2000, "attack": 280, "defense": 110, "xp": 1500, "gold": 1300},
            {"name": "Пожиратель миров", "emoji": "🌀", "hp": 2500, "attack": 260, "defense": 130, "xp": 1700, "gold": 1500},
            {"name": "Тёмный титан", "emoji": "🗿", "hp": 3000, "attack": 250, "defense": 150, "xp": 1800, "gold": 1600},
            {"name": "Void Wraith", "emoji": "👤", "hp": 1800, "attack": 350, "defense": 100, "xp": 2000, "gold": 1800},
            {"name": "Архидемон", "emoji": "😈", "hp": 2800, "attack": 300, "defense": 140, "xp": 2200, "gold": 2000},
        ],
        "boss": {"name": "🔴 Бог Хаоса", "hp": 6000, "attack": 450, "defense": 180, "xp": 5000, "gold": 5000},
        "drop_chance": 40, "drop_rates": {"epic": 20, "legendary": 80},
    },
]


def get_available_zones(level: int) -> list:
    return [z for z in ZONES if level >= z["min_level"]]


def pick_monster(zone_id: int) -> tuple:
    """Выбрать монстра. Возвращает (monster, is_boss)"""
    zone = next(z for z in ZONES if z["id"] == zone_id)
    # 8% шанс встретить мини-босса
    if random.randint(1, 100) <= 8 and zone.get("boss"):
        return zone["boss"], True
    return random.choice(zone["monsters"]), False


# ============ БАШНЯ ИСПЫТАНИЙ ============

def get_tower_monster(floor: int) -> dict:
    """Сгенерировать монстра башни для этажа"""
    is_boss = floor % 10 == 0
    mult = 2.0 if is_boss else 1.0

    names_normal = [
        "Страж", "Голем", "Призрак", "Химера", "Демон",
        "Рыцарь Тьмы", "Элементаль", "Минотавр", "Гидра", "Феникс",
    ]
    names_boss = [
        "Хранитель этажа", "Тёмный лорд", "Владыка подземелья",
        "Повелитель теней", "Древнее зло",
    ]
    emojis_normal = ["🗿", "👻", "🐉", "😈", "⚔️", "💀", "🔥", "🧌", "🐍", "🦇"]
    emojis_boss = ["👑", "🔱", "💎", "⭐", "🏆"]

    if is_boss:
        name = f"🔴 {random.choice(names_boss)} (Этаж {floor})"
        emoji = random.choice(emojis_boss)
    else:
        name = f"{random.choice(names_normal)} (Этаж {floor})"
        emoji = random.choice(emojis_normal)

    return {
        "name": name,
        "emoji": emoji,
        "hp": int((30 + floor * 18) * mult),
        "attack": int((5 + floor * 3.5) * mult),
        "defense": int((2 + floor * 1.8) * mult),
        "crit": 3.0 + floor * 0.1,
    }


def tower_rewards(floor: int) -> dict:
    """Награды за этаж башни"""
    is_boss = floor % 10 == 0
    return {
        "gold": (100 + floor * 12) * (3 if is_boss else 1),
        "xp": (15 + floor * 5) * (3 if is_boss else 1),
        "crystals": (floor // 5) + (10 if is_boss else 0),
        "drop_item": is_boss or random.randint(1, 100) <= 10 + floor // 5,
        "drop_rarity": _tower_drop_rarity(floor),
    }


def _tower_drop_rarity(floor: int) -> str:
    if floor >= 80:
        return random.choices(["epic", "legendary"], [40, 60])[0]
    if floor >= 50:
        return random.choices(["rare", "epic", "legendary"], [20, 50, 30])[0]
    if floor >= 30:
        return random.choices(["uncommon", "rare", "epic"], [20, 50, 30])[0]
    if floor >= 15:
        return random.choices(["common", "uncommon", "rare"], [20, 50, 30])[0]
    return random.choices(["common", "uncommon", "rare"], [50, 35, 15])[0]


# ============ КВЕСТЫ ============

QUEST_TEMPLATES = [
    {"type": "hunt", "target": 3, "desc": "Убей {t} монстров", "gold": 150, "crystals": 0, "xp": 50},
    {"type": "hunt", "target": 5, "desc": "Убей {t} монстров", "gold": 250, "crystals": 5, "xp": 80},
    {"type": "hunt", "target": 10, "desc": "Убей {t} монстров", "gold": 500, "crystals": 10, "xp": 150},
    {"type": "arena", "target": 1, "desc": "Выиграй {t} бой на арене", "gold": 100, "crystals": 5, "xp": 40},
    {"type": "arena", "target": 3, "desc": "Выиграй {t} боя на арене", "gold": 300, "crystals": 10, "xp": 100},
    {"type": "gacha", "target": 1, "desc": "Сделай {t} призыв", "gold": 200, "crystals": 0, "xp": 30},
    {"type": "gacha", "target": 3, "desc": "Сделай {t} призыва", "gold": 400, "crystals": 5, "xp": 60},
    {"type": "tower", "target": 3, "desc": "Пройди {t} этажа башни", "gold": 200, "crystals": 10, "xp": 100},
    {"type": "tower", "target": 5, "desc": "Пройди {t} этажей башни", "gold": 350, "crystals": 15, "xp": 150},
    {"type": "expedition", "target": 1, "desc": "Заверши {t} экспедицию", "gold": 150, "crystals": 5, "xp": 50},
    {"type": "sell", "target": 2, "desc": "Продай {t} предмета", "gold": 100, "crystals": 3, "xp": 30},
]


def generate_daily_quests(count: int = 3) -> list:
    """Сгенерировать ежедневные квесты"""
    # Берём разные типы
    types_used = set()
    quests = []
    shuffled = random.sample(QUEST_TEMPLATES, len(QUEST_TEMPLATES))
    for q in shuffled:
        if q["type"] not in types_used and len(quests) < count:
            quests.append(q.copy())
            types_used.add(q["type"])
    # Если не набрали — добираем любые
    while len(quests) < count:
        quests.append(random.choice(QUEST_TEMPLATES).copy())
    return quests


# ============ ЭКСПЕДИЦИИ ============

EXPEDITIONS = [
    {"id": "short", "name": "🏃 Быстрая вылазка", "duration": 15,
     "gold": (50, 150), "xp": (20, 50), "crystals": (0, 3), "item_chance": 5},
    {"id": "medium", "name": "🚶 Разведка", "duration": 60,
     "gold": (150, 400), "xp": (60, 150), "crystals": (2, 8), "item_chance": 18},
    {"id": "long", "name": "🗺 Дальний поход", "duration": 180,
     "gold": (400, 1000), "xp": (150, 400), "crystals": (5, 15), "item_chance": 30},
    {"id": "epic", "name": "⚔️ Великая экспедиция", "duration": 360,
     "gold": (800, 2000), "xp": (300, 800), "crystals": (10, 30), "item_chance": 45},
]


def generate_expedition_rewards(exp_id: str) -> dict:
    """Сгенерировать награды экспедиции"""
    exp = next(e for e in EXPEDITIONS if e["id"] == exp_id)
    gold = random.randint(*exp["gold"])
    xp = random.randint(*exp["xp"])
    crystals = random.randint(*exp["crystals"])
    has_item = random.randint(1, 100) <= exp["item_chance"]
    item_rarity = ""
    if has_item:
        item_rarity = random.choices(
            ["uncommon", "rare", "epic", "legendary"],
            [40, 35, 20, 5]
        )[0]
    return {"gold": gold, "xp": xp, "crystals": crystals, "item_rarity": item_rarity}


# ============ КОЛЕСО ФОРТУНЫ ============

WHEEL_PRIZES = [
    {"name": "💰 100 золота", "type": "gold", "amount": 100, "weight": 25},
    {"name": "💰 300 золота", "type": "gold", "amount": 300, "weight": 15},
    {"name": "💰 1000 золота", "type": "gold", "amount": 1000, "weight": 5},
    {"name": "💎 5 кристаллов", "type": "crystals", "amount": 5, "weight": 18},
    {"name": "💎 15 кристаллов", "type": "crystals", "amount": 15, "weight": 8},
    {"name": "💎 50 кристаллов!", "type": "crystals", "amount": 50, "weight": 2},
    {"name": "⚡ 30 энергии", "type": "energy", "amount": 30, "weight": 15},
    {"name": "⚡ Полная энергия!", "type": "energy", "amount": 100, "weight": 5},
    {"name": "🟢 Необычный предмет", "type": "item", "rarity": "uncommon", "weight": 5},
    {"name": "🔵 Редкий предмет!", "type": "item", "rarity": "rare", "weight": 4},
    {"name": "🟣 Эпический предмет!!", "type": "item", "rarity": "epic", "weight": 1},
    {"name": "🟡 ЛЕГЕНДАРНЫЙ!!!", "type": "item", "rarity": "legendary", "weight": 0.3},
    {"name": "😤 Пусто", "type": "nothing", "amount": 0, "weight": 5},
]


def spin_wheel() -> dict:
    weights = [p["weight"] for p in WHEEL_PRIZES]
    return random.choices(WHEEL_PRIZES, weights=weights)[0]


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
    ],
    "uncommon": [
        {"name": "Кольчуга", "attack": 0, "defense": 5, "hp": 15, "crit": 0},
        {"name": "Кожаная броня", "attack": 0, "defense": 4, "hp": 20, "crit": 0},
    ],
    "rare": [
        {"name": "Латные доспехи", "attack": 0, "defense": 8, "hp": 30, "crit": 0},
        {"name": "Мифриловая кольчуга", "attack": 1, "defense": 7, "hp": 25, "crit": 0},
    ],
    "epic": [
        {"name": "Доспехи Дракона", "attack": 2, "defense": 14, "hp": 50, "crit": 0},
        {"name": "Теневая мантия", "attack": 3, "defense": 10, "hp": 30, "crit": 3.0},
    ],
    "legendary": [
        {"name": "🔥 Доспехи Бога", "attack": 5, "defense": 22, "hp": 80, "crit": 2.0},
        {"name": "💀 Броня Бессмертного", "attack": 0, "defense": 25, "hp": 100, "crit": 0},
    ],
}

ACCESSORIES = {
    "common": [
        {"name": "Медное кольцо", "attack": 1, "defense": 1, "hp": 3, "crit": 0},
        {"name": "Кожаный браслет", "attack": 2, "defense": 0, "hp": 5, "crit": 0},
    ],
    "uncommon": [
        {"name": "Серебряное кольцо", "attack": 2, "defense": 2, "hp": 8, "crit": 1.0},
        {"name": "Амулет удачи", "attack": 1, "defense": 1, "hp": 5, "crit": 2.0},
    ],
    "rare": [
        {"name": "Кольцо мощи", "attack": 5, "defense": 3, "hp": 15, "crit": 1.0},
        {"name": "Браслет теней", "attack": 4, "defense": 1, "hp": 10, "crit": 4.0},
    ],
    "epic": [
        {"name": "Кольцо Дракона", "attack": 8, "defense": 5, "hp": 25, "crit": 3.0},
        {"name": "Печать Короля", "attack": 6, "defense": 6, "hp": 30, "crit": 2.0},
    ],
    "legendary": [
        {"name": "🔥 Перстень Всевластия", "attack": 15, "defense": 8, "hp": 40, "crit": 5.0},
        {"name": "💀 Ожерелье Смерти", "attack": 18, "defense": 3, "hp": 20, "crit": 8.0},
    ],
}


# ============ ГАЧА ============
GACHA_FREE_COST = 500
GACHA_PREM_COST = 50
GACHA_10X_COST = 450

GACHA_RATES_FREE = {"common": 50, "uncommon": 30, "rare": 15, "epic": 4, "legendary": 1}
GACHA_RATES_PREMIUM = {"uncommon": 30, "rare": 40, "epic": 25, "legendary": 5}


def _pick_rarity(rates: dict) -> str:
    roll = random.randint(1, 100)
    cumulative = 0
    for rarity, chance in rates.items():
        cumulative += chance
        if roll <= cumulative:
            return rarity
    return list(rates.keys())[-1]


def generate_item(rarity: str, item_type: str = None) -> dict:
    if not item_type:
        item_type = random.choice(["weapon", "armor", "accessory"])
    templates = {"weapon": WEAPONS, "armor": ARMORS, "accessory": ACCESSORIES}
    pool = templates[item_type].get(rarity, templates[item_type]["common"])
    base = random.choice(pool)

    def vary(val):
        if val == 0: return 0
        return max(1, int(val * random.uniform(0.85, 1.15)))

    return {
        "item_type": item_type, "name": base["name"], "rarity": rarity,
        "bonus_attack": vary(base["attack"]), "bonus_defense": vary(base["defense"]),
        "bonus_hp": vary(base["hp"]), "bonus_crit": round(base["crit"] * random.uniform(0.9, 1.1), 1),
    }


def gacha_pull(is_premium=False):
    rarity = _pick_rarity(GACHA_RATES_PREMIUM if is_premium else GACHA_RATES_FREE)
    return generate_item(rarity)


def gacha_pull_10x():
    items = [gacha_pull(is_premium=True) for _ in range(10)]
    if not any(i["rarity"] in ("epic", "legendary") for i in items):
        items[-1] = generate_item(random.choice(["epic", "legendary"]))
    return items


# ============ БОЕВАЯ СИСТЕМА ============

def simulate_combat(attacker: dict, defender: dict) -> dict:
    atk_hp, def_hp = attacker["hp"], defender["hp"]
    log, total_dealt, total_received, crits, rounds = [], 0, 0, 0, 0

    while atk_hp > 0 and def_hp > 0 and rounds < 25:
        rounds += 1
        is_crit = random.random() * 100 < attacker.get("crit", 5)
        dmg = max(1, int(attacker["attack"] * random.uniform(0.8, 1.2) - defender["defense"] * 0.3))
        if is_crit:
            dmg *= 2
            crits += 1
        def_hp -= dmg
        total_dealt += dmg
        log.append(f"⚔️ Ты: -{dmg} HP{'💥' if is_crit else ''}")
        if def_hp <= 0:
            break
        dmg_b = max(1, int(defender["attack"] * random.uniform(0.8, 1.2) - attacker["defense"] * 0.3))
        atk_hp -= dmg_b
        total_received += dmg_b
        log.append(f"👹 Враг: -{dmg_b} HP")

    return {
        "won": def_hp <= 0, "rounds": rounds, "log": log[:8],
        "damage_dealt": total_dealt, "damage_received": total_received,
        "crits": crits, "hp_left": max(0, atk_hp), "hp_max": attacker["hp"],
    }


def get_total_stats(base: dict, equip: dict) -> dict:
    return {
        "hp": base["max_hp"] + equip.get("hp", 0),
        "attack": base["attack"] + equip.get("attack", 0),
        "defense": base["defense"] + equip.get("defense", 0),
        "crit": base["crit"] + equip.get("crit", 0),
    }


# ============ ХЕЛПЕРЫ ============
TYPE_EMOJI = {"weapon": "🗡", "armor": "🛡", "accessory": "💍"}
TYPE_NAMES = {"weapon": "Оружие", "armor": "Броня", "accessory": "Аксессуар"}

def hp_bar(cur, mx, length=10):
    r = max(0, min(1, cur / mx)) if mx > 0 else 0
    f = int(r * length)
    return "█" * f + "░" * (length - f)

def format_item_short(item):
    return f"{TYPE_EMOJI.get(item.get('item_type',''),'📦')} {RARITY_EMOJI.get(item.get('rarity','common'),'⚪')} {item.get('name','???')}"

def format_item_stats(item):
    p = []
    if item.get("bonus_attack", 0): p.append(f"+{item['bonus_attack']}ATK")
    if item.get("bonus_defense", 0): p.append(f"+{item['bonus_defense']}DEF")
    if item.get("bonus_hp", 0): p.append(f"+{item['bonus_hp']}HP")
    if item.get("bonus_crit", 0): p.append(f"+{item['bonus_crit']}%КР")
    return ", ".join(p) if p else "—"

def try_drop_item(zone_id):
    zone = next((z for z in ZONES if z["id"] == zone_id), None)
    if not zone: return None
    if random.randint(1, 100) > zone["drop_chance"]: return None
    return generate_item(_pick_rarity(zone["drop_rates"]))
