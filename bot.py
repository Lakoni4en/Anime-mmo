"""
⚔️ Текстовая MMO RPG — Telegram бот
Охота, Арена PvP, Гача, Магазин (Stars), Топ игроков
"""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import config
import database as db
from game_data import (
    CLASSES, ZONES, RARITY_EMOJI, RARITY_NAMES, SELL_PRICES,
    TYPE_EMOJI, TYPE_NAMES,
    get_class_stats, get_available_zones, pick_monster, xp_for_level,
    simulate_combat, get_total_stats, gacha_pull, gacha_pull_10x,
    hp_bar, format_item_short, format_item_stats, try_drop_item,
    GACHA_FREE_COST, GACHA_PREM_COST, GACHA_10X_COST,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# ============ КЛАВИАТУРЫ ============

def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺 Охота", callback_data="hunt"),
         InlineKeyboardButton(text="⚔️ Арена", callback_data="arena")],
        [InlineKeyboardButton(text="🎰 Призыв", callback_data="gacha"),
         InlineKeyboardButton(text="📦 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="prof"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="🏪 Магазин", callback_data="shop")],
    ])


def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")]
    ])


def kb_class_select() -> InlineKeyboardMarkup:
    buttons = []
    for cid, c in CLASSES.items():
        buttons.append([InlineKeyboardButton(text=f"{c['name']}", callback_data=f"cls_{cid}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_zones(level: int) -> InlineKeyboardMarkup:
    zones = get_available_zones(level)
    buttons = []
    for z in zones:
        buttons.append([InlineKeyboardButton(
            text=f"{z['name']} (Lv.{z['min_level']}+)",
            callback_data=f"hz_{z['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_player_combat_stats(user_id: int) -> dict:
    """Полные боевые характеристики игрока"""
    player = await db.get_player(user_id)
    if not player:
        return {}
    base = get_class_stats(player["class"], player["level"])
    equip = await db.get_equipment_bonuses(user_id)
    return get_total_stats(base, equip)


# ============ /START — СОЗДАНИЕ ПЕРСОНАЖА ============

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    player = await db.get_player(message.from_user.id)

    if player and player["class"]:
        # Уже есть персонаж
        await db.update_player_name(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.first_name or "Воин",
        )
        # Ежедневный бонус
        daily = await db.check_daily(message.from_user.id)
        daily_text = ""
        if daily:
            ds = daily["daily_streak"]
            bonus_gold = config.DAILY_GOLD + (ds * 10)
            bonus_crystals = config.DAILY_CRYSTALS + (1 if ds >= 3 else 0)
            await db.add_gold(message.from_user.id, bonus_gold)
            await db.add_crystals(message.from_user.id, bonus_crystals)
            daily_text = (
                f"\n🌅 <b>Ежедневный бонус!</b>\n"
                f"💰 +{bonus_gold} золота  💎 +{bonus_crystals} кристаллов\n"
                f"📅 Дней подряд: {ds}\n"
            )

        player = await db.get_player(message.from_user.id)
        cls = CLASSES[player["class"]]
        energy = db.calculate_energy(player)
        text = (
            f"⚔️ <b>Добро пожаловать, {cls['name']} {message.from_user.first_name}!</b>\n\n"
            f"📊 Lv.{player['level']}  💰{player['gold']}  💎{player['crystals']}  "
            f"⚡{energy}/{player['max_energy']}\n"
            f"{daily_text}\n"
            f"Выбери действие:"
        )
        await message.answer(text, reply_markup=kb_main())
    else:
        # Новый игрок — выбор класса
        text = (
            "⚔️ <b>Добро пожаловать в мир приключений!</b>\n\n"
            "Выбери свой класс:\n\n"
        )
        for cid, c in CLASSES.items():
            text += (
                f"{c['name']}\n"
                f"<i>{c['desc']}</i>\n"
                f"❤️{c['base_hp']}  ⚔️{c['base_attack']}  "
                f"🛡{c['base_defense']}  💥{c['base_crit']}%\n\n"
            )
        await message.answer(text, reply_markup=kb_class_select())


@dp.callback_query(F.data.startswith("cls_"))
async def cb_select_class(callback: types.CallbackQuery):
    """Выбор класса"""
    class_id = callback.data.replace("cls_", "")
    if class_id not in CLASSES:
        await callback.answer("Ошибка!", show_alert=True)
        return

    await callback.answer()

    # Проверяем что игрок ещё не создан
    player = await db.get_player(callback.from_user.id)
    if player and player["class"]:
        await callback.message.edit_text("У тебя уже есть персонаж!", reply_markup=kb_main())
        return

    await db.create_player(
        callback.from_user.id,
        callback.from_user.username or "",
        callback.from_user.first_name or "Воин",
        class_id,
    )

    cls = CLASSES[class_id]
    stats = get_class_stats(class_id, 1)
    text = (
        f"🎉 <b>Персонаж создан!</b>\n\n"
        f"{cls['name']} <b>{callback.from_user.first_name}</b>\n\n"
        f"❤️ HP: {stats['max_hp']}\n"
        f"⚔️ Атака: {stats['attack']}\n"
        f"🛡 Защита: {stats['defense']}\n"
        f"💥 Крит: {stats['crit']}%\n\n"
        f"💰 500 золота на старте\n"
        f"⚡ 100 энергии\n\n"
        f"Удачи, воин! ⚔️"
    )
    await callback.message.edit_text(text, reply_markup=kb_main())


# ============ МЕНЮ ============

@dp.callback_query(F.data == "menu")
async def cb_menu(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player or not player["class"]:
        await callback.message.edit_text("Нажми /start чтобы создать персонажа!")
        return

    cls = CLASSES[player["class"]]
    energy = db.calculate_energy(player)
    text = (
        f"{cls['name']} <b>{player['first_name']}</b> "
        f"(Lv.{player['level']})\n\n"
        f"💰 {player['gold']}  💎 {player['crystals']}  ⚡ {energy}/{player['max_energy']}\n\n"
        f"Выбери действие:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb_main())
    except Exception:
        await callback.message.answer(text, reply_markup=kb_main())


# ============ ОХОТА (PvE) ============

@dp.callback_query(F.data == "hunt")
async def cb_hunt(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player or not player["class"]:
        return

    energy = db.calculate_energy(player)
    text = (
        f"🗺 <b>Охота</b>\n\n"
        f"⚡ Энергия: {energy}/{player['max_energy']} "
        f"(расход: {config.HUNT_ENERGY_COST})\n\n"
        f"Выбери зону:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb_zones(player["level"]))
    except Exception:
        await callback.message.answer(text, reply_markup=kb_zones(player["level"]))


@dp.callback_query(F.data.startswith("hz_"))
async def cb_hunt_zone(callback: types.CallbackQuery):
    """Охота в зоне"""
    zone_id = int(callback.data.replace("hz_", ""))
    user_id = callback.from_user.id

    player = await db.get_player(user_id)
    if not player or not player["class"]:
        await callback.answer("Сначала создай персонажа! /start", show_alert=True)
        return

    # Проверка зоны
    zone = next((z for z in ZONES if z["id"] == zone_id), None)
    if not zone or player["level"] < zone["min_level"]:
        await callback.answer(f"Нужен уровень {zone['min_level']}!", show_alert=True)
        return

    # Проверка энергии
    energy = db.calculate_energy(player)
    if energy < config.HUNT_ENERGY_COST:
        await callback.answer(
            f"⚡ Не хватает энергии! ({energy}/{config.HUNT_ENERGY_COST})\n"
            f"Подожди или купи в магазине.",
            show_alert=True
        )
        return

    await callback.answer()

    # Тратим энергию
    await db.spend_energy(user_id, config.HUNT_ENERGY_COST, energy)

    # Выбираем монстра
    monster = pick_monster(zone_id)

    # Характеристики игрока
    player_stats = await get_player_combat_stats(user_id)

    # Характеристики монстра
    monster_stats = {
        "hp": monster["hp"],
        "attack": monster["attack"],
        "defense": monster["defense"],
        "crit": 3.0,
    }

    # БОЙ
    result = simulate_combat(player_stats, monster_stats)

    if result["won"]:
        # Победа
        gold = monster["gold"]
        xp = monster["xp"]

        await db.add_gold(user_id, gold)
        new_levels = await db.add_xp(user_id, xp)
        await db.record_hunt(user_id)

        # Дроп предмета
        drop = try_drop_item(zone_id)
        drop_text = ""
        if drop:
            await db.add_item(user_id, drop)
            drop_text = (
                f"\n🎁 <b>Дроп!</b>\n"
                f"  {format_item_short(drop)}\n"
                f"  {format_item_stats(drop)}\n"
            )

        # Повышение уровня
        lvl_text = ""
        if new_levels:
            for lvl in new_levels:
                await db.add_gold(user_id, config.GOLD_PER_LEVELUP)
                await db.add_crystals(user_id, config.CRYSTALS_PER_LEVELUP)
                lvl_text += (
                    f"\n🎉 <b>Уровень {lvl}!</b>"
                    f" +{config.GOLD_PER_LEVELUP}💰 +{config.CRYSTALS_PER_LEVELUP}💎"
                )

        # Лог боя (показываем 4-6 строк)
        log_lines = result["log"][:6]
        log_text = "\n".join(log_lines)

        new_energy = db.calculate_energy(await db.get_player(user_id))
        text = (
            f"⚔️ <b>Бой с {monster['emoji']} {monster['name']}</b>\n\n"
            f"{log_text}\n\n"
            f"✅ <b>ПОБЕДА!</b> ({result['rounds']} раундов)\n"
            f"❤️ HP: {result['hp_left']}/{result['hp_max']} "
            f"[{hp_bar(result['hp_left'], result['hp_max'])}]\n\n"
            f"💰 +{gold}  ✨ +{xp} XP\n"
            f"{drop_text}{lvl_text}\n"
            f"⚡ Энергия: {new_energy}/{player['max_energy']}"
        )
    else:
        # Поражение
        log_lines = result["log"][:6]
        log_text = "\n".join(log_lines)
        new_energy = db.calculate_energy(await db.get_player(user_id))

        text = (
            f"⚔️ <b>Бой с {monster['emoji']} {monster['name']}</b>\n\n"
            f"{log_text}\n\n"
            f"❌ <b>ПОРАЖЕНИЕ!</b> ({result['rounds']} раундов)\n"
            f"Монстр оказался слишком силён...\n\n"
            f"💡 Улучши экипировку или выбери зону полегче!\n"
            f"⚡ Энергия: {new_energy}/{player['max_energy']}"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗺 Ещё охота", callback_data="hunt")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============ АРЕНА (PvP) ============

@dp.callback_query(F.data == "arena")
async def cb_arena(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player or not player["class"]:
        return

    fights_left = await db.get_arena_fights_left(callback.from_user.id)

    text = (
        f"⚔️ <b>Арена PvP</b>\n\n"
        f"🏅 Рейтинг: {player['arena_rating']}\n"
        f"📊 Победы: {player['arena_wins']} | Поражения: {player['arena_losses']}\n"
        f"🎫 Боёв сегодня: {fights_left}/{config.ARENA_FIGHTS_PER_DAY}\n\n"
        f"Награда за победу: 💰{config.ARENA_WIN_GOLD} 💎{config.ARENA_WIN_CRYSTALS}"
    )

    buttons = []
    if fights_left > 0:
        buttons.append([InlineKeyboardButton(text="⚔️ Сразиться!", callback_data="afight")])
    else:
        buttons.append([InlineKeyboardButton(text="🚫 Бои закончились (завтра)", callback_data="noop")])
    buttons.append([InlineKeyboardButton(text="🏆 Рейтинг арены", callback_data="top_arena")])
    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="menu")])

    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data == "afight")
async def cb_arena_fight(callback: types.CallbackQuery):
    """Бой на арене"""
    user_id = callback.from_user.id
    fights_left = await db.get_arena_fights_left(user_id)
    if fights_left <= 0:
        await callback.answer("Бои на сегодня закончились!", show_alert=True)
        return

    opponent = await db.get_arena_opponent(user_id)
    if not opponent:
        await callback.answer("Нет доступных противников. Позови друзей!", show_alert=True)
        return

    await callback.answer()

    # Статы
    my_stats = await get_player_combat_stats(user_id)
    opp_base = get_class_stats(opponent["class"], opponent["level"])
    opp_equip = await db.get_equipment_bonuses(opponent["user_id"])
    opp_stats = get_total_stats(opp_base, opp_equip)

    # Бой
    result = simulate_combat(my_stats, opp_stats)

    opp_cls = CLASSES[opponent["class"]]
    opp_name = opponent["first_name"] or opponent["username"] or f"ID:{opponent['user_id']}"

    if result["won"]:
        await db.record_arena_fight(user_id, True, config.ARENA_WIN_RATING)
        await db.add_gold(user_id, config.ARENA_WIN_GOLD)
        await db.add_crystals(user_id, config.ARENA_WIN_CRYSTALS)

        combat_log = "\n".join(result["log"][:5])
        text = (
            f"⚔️ <b>Арена: Ты vs {opp_cls['name']} {opp_name} (Lv.{opponent['level']})</b>\n\n"
            f"Твои статы: ❤️{my_stats['hp']} ⚔️{my_stats['attack']} 🛡{my_stats['defense']}\n"
            f"Противник: ❤️{opp_stats['hp']} ⚔️{opp_stats['attack']} 🛡{opp_stats['defense']}\n\n"
            f"{combat_log}\n\n"
            f"🏆 <b>ПОБЕДА!</b> ({result['rounds']} раундов)\n"
            f"❤️ HP: {result['hp_left']}/{result['hp_max']}\n\n"
            f"📈 +{config.ARENA_WIN_RATING} рейтинга\n"
            f"💰 +{config.ARENA_WIN_GOLD}  💎 +{config.ARENA_WIN_CRYSTALS}"
        )
    else:
        await db.record_arena_fight(user_id, False, config.ARENA_LOSE_RATING)

        combat_log = "\n".join(result["log"][:5])
        text = (
            f"⚔️ <b>Арена: Ты vs {opp_cls['name']} {opp_name} (Lv.{opponent['level']})</b>\n\n"
            f"Твои статы: ❤️{my_stats['hp']} ⚔️{my_stats['attack']} 🛡{my_stats['defense']}\n"
            f"Противник: ❤️{opp_stats['hp']} ⚔️{opp_stats['attack']} 🛡{opp_stats['defense']}\n\n"
            f"{combat_log}\n\n"
            f"❌ <b>ПОРАЖЕНИЕ!</b> ({result['rounds']} раундов)\n\n"
            f"📉 -{config.ARENA_LOSE_RATING} рейтинга"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Ещё бой", callback_data="afight")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============ ГАЧА ============

@dp.callback_query(F.data == "gacha")
async def cb_gacha(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player or not player["class"]:
        return

    text = (
        f"🎰 <b>Призыв экипировки</b>\n\n"
        f"💰 Золото: {player['gold']}  💎 Кристаллы: {player['crystals']}\n\n"
        f"🪙 <b>Обычный призыв</b> — {GACHA_FREE_COST} 💰\n"
        f"  ⚪50% 🟢30% 🔵15% 🟣4% 🟡1%\n\n"
        f"💎 <b>Премиум призыв</b> — {GACHA_PREM_COST} 💎\n"
        f"  🟢30% 🔵40% 🟣25% 🟡5%\n\n"
        f"💎 <b>10x Призыв</b> — {GACHA_10X_COST} 💎\n"
        f"  Гарантия 🟣 Epic+!"
    )

    buttons = [
        [InlineKeyboardButton(text=f"🪙 Обычный ({GACHA_FREE_COST} 💰)", callback_data="gfree")],
        [InlineKeyboardButton(text=f"💎 Премиум ({GACHA_PREM_COST} 💎)", callback_data="gprem")],
        [InlineKeyboardButton(text=f"💎 10x Призыв ({GACHA_10X_COST} 💎)", callback_data="g10x")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ]

    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data == "gfree")
async def cb_gacha_free(callback: types.CallbackQuery):
    """Обычный призыв за золото"""
    ok = await db.spend_gold(callback.from_user.id, GACHA_FREE_COST)
    if not ok:
        await callback.answer(f"Не хватает золота! Нужно {GACHA_FREE_COST} 💰", show_alert=True)
        return
    await callback.answer()

    item = gacha_pull(is_premium=False)
    await db.add_item(callback.from_user.id, item)

    text = (
        f"🎰 <b>Обычный призыв!</b>\n\n"
        f"Ты получаешь...\n\n"
        f"  {format_item_short(item)}\n"
        f"  {RARITY_EMOJI[item['rarity']]} {RARITY_NAMES[item['rarity']]}\n"
        f"  📊 {format_item_stats(item)}\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Ещё призыв", callback_data="gacha")],
        [InlineKeyboardButton(text="📦 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "gprem")
async def cb_gacha_premium(callback: types.CallbackQuery):
    """Премиум призыв за кристаллы"""
    ok = await db.spend_crystals(callback.from_user.id, GACHA_PREM_COST)
    if not ok:
        await callback.answer(f"Не хватает кристаллов! Нужно {GACHA_PREM_COST} 💎", show_alert=True)
        return
    await callback.answer()

    item = gacha_pull(is_premium=True)
    await db.add_item(callback.from_user.id, item)

    text = (
        f"💎 <b>Премиум призыв!</b>\n\n"
        f"✨ Ты получаешь...\n\n"
        f"  {format_item_short(item)}\n"
        f"  {RARITY_EMOJI[item['rarity']]} {RARITY_NAMES[item['rarity']]}\n"
        f"  📊 {format_item_stats(item)}\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Ещё призыв", callback_data="gacha")],
        [InlineKeyboardButton(text="📦 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@dp.callback_query(F.data == "g10x")
async def cb_gacha_10x(callback: types.CallbackQuery):
    """10x премиум призыв"""
    ok = await db.spend_crystals(callback.from_user.id, GACHA_10X_COST)
    if not ok:
        await callback.answer(f"Не хватает кристаллов! Нужно {GACHA_10X_COST} 💎", show_alert=True)
        return
    await callback.answer()

    items = gacha_pull_10x()
    lines = []
    for item in items:
        await db.add_item(callback.from_user.id, item)
        lines.append(f"  {format_item_short(item)} — {format_item_stats(item)}")

    text = (
        f"💎 <b>10x Премиум призыв!</b>\n\n"
        + "\n".join(lines)
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Ещё призыв", callback_data="gacha")],
        [InlineKeyboardButton(text="📦 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============ ИНВЕНТАРЬ ============

@dp.callback_query(F.data == "inv")
async def cb_inventory(callback: types.CallbackQuery):
    await callback.answer()
    await show_inventory(callback.from_user.id, callback.message)


@dp.callback_query(F.data.startswith("invp_"))
async def cb_inv_page(callback: types.CallbackQuery):
    await callback.answer()
    page = int(callback.data.replace("invp_", ""))
    await show_inventory(callback.from_user.id, callback.message, page=page)


async def show_inventory(user_id: int, message: types.Message, page: int = 1):
    items = await db.get_inventory(user_id)

    if not items:
        text = "📦 <b>Инвентарь пуст!</b>\n\nСходи на охоту или сделай призыв 🎰"
        try:
            await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗺 Охота", callback_data="hunt"),
                 InlineKeyboardButton(text="🎰 Призыв", callback_data="gacha")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
            ]))
        except Exception:
            await message.answer(text, reply_markup=kb_back())
        return

    # Разделяем на надетые и в сумке
    equipped = [i for i in items if i["is_equipped"]]
    bag = [i for i in items if not i["is_equipped"]]

    lines = ["📦 <b>Инвентарь</b>\n"]

    if equipped:
        lines.append("🔧 <b>Надето:</b>")
        for item in equipped:
            lines.append(f"  {format_item_short(item)} — {format_item_stats(item)}")
        lines.append("")

    # Пагинация сумки
    per_page = 8
    total_pages = max(1, (len(bag) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_items = bag[start:start + per_page]

    if page_items:
        lines.append(f"🎒 <b>Сумка</b> ({len(bag)} шт.):")
        for item in page_items:
            lines.append(f"  {format_item_short(item)} — {format_item_stats(item)}")

    text = "\n".join(lines)

    # Кнопки для предметов в сумке
    buttons = []
    for item in page_items:
        buttons.append([InlineKeyboardButton(
            text=f"👆 {item['name']}", callback_data=f"itm_{item['id']}"
        )])

    # Навигация
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"invp_{page - 1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"invp_{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="🏠 Меню", callback_data="menu")])

    try:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception:
        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("itm_"))
async def cb_item_detail(callback: types.CallbackQuery):
    """Детали предмета"""
    item_id = int(callback.data.replace("itm_", ""))
    item = await db.get_item(item_id)
    if not item or item["user_id"] != callback.from_user.id:
        await callback.answer("Предмет не найден!", show_alert=True)
        return
    await callback.answer()

    rarity = item["rarity"]
    sell_price = SELL_PRICES.get(rarity, 30)

    text = (
        f"{format_item_short(item)}\n\n"
        f"📊 <b>Характеристики:</b>\n"
        f"  {RARITY_EMOJI[rarity]} {RARITY_NAMES[rarity]}\n"
        f"  {TYPE_EMOJI.get(item['item_type'], '📦')} {TYPE_NAMES.get(item['item_type'], '???')}\n"
        f"  {format_item_stats(item)}\n\n"
        f"💰 Цена продажи: {sell_price} золота"
    )

    buttons = []
    if not item["is_equipped"]:
        buttons.append([
            InlineKeyboardButton(text="✅ Надеть", callback_data=f"eqp_{item_id}"),
            InlineKeyboardButton(text=f"💰 Продать ({sell_price})", callback_data=f"sel_{item_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="📦 Инвентарь", callback_data="inv")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("eqp_"))
async def cb_equip(callback: types.CallbackQuery):
    """Надеть предмет"""
    item_id = int(callback.data.replace("eqp_", ""))
    item = await db.get_item(item_id)
    if not item or item["user_id"] != callback.from_user.id:
        await callback.answer("Ошибка!", show_alert=True)
        return

    await db.equip_item(callback.from_user.id, item_id)
    await callback.answer(f"✅ {item['name']} надето!", show_alert=True)
    await show_inventory(callback.from_user.id, callback.message)


@dp.callback_query(F.data.startswith("sel_"))
async def cb_sell(callback: types.CallbackQuery):
    """Продать предмет"""
    item_id = int(callback.data.replace("sel_", ""))
    gold = await db.sell_item(callback.from_user.id, item_id)
    if gold == 0:
        await callback.answer("Нельзя продать! (надето или не найдено)", show_alert=True)
        return

    await callback.answer(f"💰 Продано за {gold} золота!", show_alert=True)
    await show_inventory(callback.from_user.id, callback.message)


# ============ ПРОФИЛЬ ============

@dp.callback_query(F.data == "prof")
@dp.message(Command("profile"))
async def cb_profile(event: types.CallbackQuery | types.Message):
    if isinstance(event, types.CallbackQuery):
        await event.answer()
        user_id = event.from_user.id
        msg = event.message
        edit = True
    else:
        user_id = event.from_user.id
        msg = event
        edit = False

    player = await db.get_player(user_id)
    if not player or not player["class"]:
        return

    cls = CLASSES[player["class"]]
    base = get_class_stats(player["class"], player["level"])
    equip = await db.get_equipment_bonuses(user_id)
    total = get_total_stats(base, equip)
    energy = db.calculate_energy(player)
    xp_need = xp_for_level(player["level"])
    equipped = await db.get_equipped_items(user_id)
    inv_count = await db.count_inventory(user_id)

    equip_lines = ""
    for slot in ["weapon", "armor", "accessory"]:
        item = next((i for i in equipped if i["item_type"] == slot), None)
        if item:
            equip_lines += f"  {format_item_short(item)} — {format_item_stats(item)}\n"
        else:
            equip_lines += f"  {TYPE_EMOJI[slot]} <i>пусто</i>\n"

    text = (
        f"{cls['name']} <b>{player['first_name']}</b>\n\n"
        f"📊 <b>Уровень {player['level']}</b>\n"
        f"  ✨ XP: {player['xp']}/{xp_need} [{hp_bar(player['xp'], xp_need)}]\n\n"
        f"⚔️ <b>Характеристики:</b>\n"
        f"  ❤️ HP: {total['hp']}  (база {base['max_hp']} +{equip.get('hp', 0)})\n"
        f"  ⚔️ ATK: {total['attack']}  (база {base['attack']} +{equip.get('attack', 0)})\n"
        f"  🛡 DEF: {total['defense']}  (база {base['defense']} +{equip.get('defense', 0)})\n"
        f"  💥 КРИТ: {total['crit']:.1f}%\n\n"
        f"💰 Золото: {player['gold']}  💎 Кристаллы: {player['crystals']}\n"
        f"⚡ Энергия: {energy}/{player['max_energy']}\n\n"
        f"🔧 <b>Экипировка:</b>\n{equip_lines}\n"
        f"📦 В инвентаре: {inv_count} предметов\n"
        f"🏅 Рейтинг арены: {player['arena_rating']}\n"
        f"⚔️ Побед/Поражений: {player['arena_wins']}/{player['arena_losses']}\n"
        f"🗺 Охот: {player['total_hunts']}  ☠️ Убийств: {player['total_kills']}\n"
        f"📅 Дней подряд: {player['daily_streak']}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Инвентарь", callback_data="inv")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    if edit:
        try:
            await msg.edit_text(text, reply_markup=keyboard)
        except Exception:
            await msg.answer(text, reply_markup=keyboard)
    else:
        await msg.answer(text, reply_markup=keyboard)


# ============ ТОП ИГРОКОВ ============

@dp.callback_query(F.data == "top")
async def cb_top(callback: types.CallbackQuery):
    await callback.answer()
    await show_top_level(callback.from_user.id, callback.message)


@dp.callback_query(F.data == "top_arena")
async def cb_top_arena(callback: types.CallbackQuery):
    await callback.answer()
    await show_top_arena(callback.from_user.id, callback.message)


async def show_top_level(user_id: int, message: types.Message):
    leaders = await db.get_leaderboard_xp(10)
    rank = await db.get_player_rank(user_id)

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, p in enumerate(leaders):
        medal = medals[i] if i < 3 else f"#{i+1}"
        cls_emoji = CLASSES.get(p["class"], {}).get("name", "?").split()[0]
        name = p["first_name"] or p["username"] or "???"
        lines.append(
            f"{medal} {cls_emoji} <b>{name}</b> — Lv.{p['level']}  "
            f"⚔️{p['arena_rating']}  ☠️{p['total_kills']}"
        )

    text = "🏆 <b>Топ игроков (уровень)</b>\n\n"
    text += "\n".join(lines) if lines else "Пока пусто..."
    text += f"\n\n👤 Твоя позиция: #{rank}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Топ арены", callback_data="top_arena")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    try:
        await message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await message.answer(text, reply_markup=keyboard)


async def show_top_arena(user_id: int, message: types.Message):
    leaders = await db.get_leaderboard_arena(10)

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, p in enumerate(leaders):
        medal = medals[i] if i < 3 else f"#{i+1}"
        cls_emoji = CLASSES.get(p["class"], {}).get("name", "?").split()[0]
        name = p["first_name"] or p["username"] or "???"
        wr = round(p["arena_wins"] / max(1, p["arena_wins"] + p["arena_losses"]) * 100)
        lines.append(
            f"{medal} {cls_emoji} <b>{name}</b> — 🏅{p['arena_rating']}  "
            f"W/L: {p['arena_wins']}/{p['arena_losses']} ({wr}%)"
        )

    text = "⚔️ <b>Топ арены (рейтинг)</b>\n\n"
    text += "\n".join(lines) if lines else "Пока пусто..."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Топ по уровню", callback_data="top")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ])

    try:
        await message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await message.answer(text, reply_markup=keyboard)


# ============ МАГАЗИН (STARS) ============

@dp.callback_query(F.data == "shop")
async def cb_shop(callback: types.CallbackQuery):
    await callback.answer()
    player = await db.get_player(callback.from_user.id)
    if not player:
        return

    text = (
        f"🏪 <b>Магазин</b>\n\n"
        f"💰 Золото: {player['gold']}  💎 Кристаллы: {player['crystals']}\n\n"
        f"<b>Купить за Telegram Stars ⭐:</b>\n\n"
        f"💎 50 кристаллов — 25 ⭐\n"
        f"💎 150 кристаллов — 65 ⭐ <i>(+15 бонус)</i>\n"
        f"💎 500 кристаллов — 200 ⭐ <i>(+75 бонус)</i>\n"
        f"⚡ {config.MAX_ENERGY} энергии — 10 ⭐\n"
    )

    buttons = [
        [InlineKeyboardButton(text="💎 50 кристаллов (25 ⭐)", callback_data="buy_c50")],
        [InlineKeyboardButton(text="💎 150 кристаллов (65 ⭐)", callback_data="buy_c150")],
        [InlineKeyboardButton(text="💎 500 кристаллов (200 ⭐)", callback_data="buy_c500")],
        [InlineKeyboardButton(text=f"⚡ {config.MAX_ENERGY} энергии (10 ⭐)", callback_data="buy_eng")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu")],
    ]

    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("buy_"))
async def cb_buy(callback: types.CallbackQuery):
    """Покупка за Stars"""
    product_id = callback.data.replace("buy_", "")
    shop = config.STARS_SHOP

    product_map = {
        "c50": "crystals_50",
        "c150": "crystals_150",
        "c500": "crystals_500",
        "eng": "energy_full",
    }

    product_key = product_map.get(product_id)
    if not product_key or product_key not in shop:
        await callback.answer("Ошибка!", show_alert=True)
        return

    product = shop[product_key]
    await callback.answer()

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=product["label"],
        description=f"Покупка в RPG игре",
        payload=f"{product_key}_{callback.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label=product["label"], amount=product["stars"])],
    )


@dp.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    """Обработка успешной оплаты"""
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    user_id = message.from_user.id

    if "crystals" in payload:
        amount_key = "_".join(parts[:2])  # crystals_50 etc
        product = config.STARS_SHOP.get(amount_key)
        if product:
            await db.add_crystals(user_id, product["crystals"])
            await message.answer(
                f"🎉 <b>Покупка успешна!</b>\n\n"
                f"💎 +{product['crystals']} кристаллов\n\n"
                f"Потрать их на призыв экипировки! 🎰",
                reply_markup=kb_main()
            )
    elif "energy" in payload:
        await db.set_energy(user_id, config.MAX_ENERGY)
        await message.answer(
            f"🎉 <b>Энергия восстановлена!</b>\n\n"
            f"⚡ {config.MAX_ENERGY}/{config.MAX_ENERGY}\n\n"
            f"Вперёд на охоту! 🗺",
            reply_markup=kb_main()
        )


# ============ ТЕКСТ ============

@dp.callback_query(F.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "📋 <b>Команды:</b>\n\n"
        "/start — Меню / создать персонажа\n"
        "/profile — Твой профиль\n"
        "/top — Топ игроков\n"
        "/help — Эта справка\n\n"
        "🎮 <b>Как играть:</b>\n"
        "🗺 <b>Охота</b> — бей монстров, получай XP, золото и лут\n"
        "⚔️ <b>Арена</b> — PvP бои с другими игроками\n"
        "🎰 <b>Призыв</b> — гача для получения экипировки\n"
        "📦 <b>Инвентарь</b> — надевай и продавай предметы\n"
        "🏪 <b>Магазин</b> — покупай кристаллы за Stars\n"
    )
    await message.answer(text, reply_markup=kb_main())


@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    await show_top_level(message.from_user.id, message)


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    stats = await db.get_bot_stats()
    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Игроков: {stats['total_players']}\n"
        f"🗺 Охот: {stats['total_hunts']}\n"
        f"⚔️ Боёв арены: {stats['total_arena_fights']}"
    )


@dp.message(F.text)
async def handle_text(message: types.Message):
    player = await db.get_player(message.from_user.id)
    if not player or not player["class"]:
        await message.answer("👋 Нажми /start чтобы создать персонажа!")
    else:
        await message.answer("⚔️ Используй кнопки для игры!", reply_markup=kb_main())


# ============ ЗАПУСК ============

async def main():
    logger.info("🗄 Инициализация БД...")
    await db.init_db()
    logger.info("⚔️ Запуск RPG бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
