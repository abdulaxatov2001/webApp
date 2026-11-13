"""
Dice Duel Widget Handler — Bot API 10.4
sendWidget + WidgetQuery orqali ishlaydi
"""
import random
import json
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, Update
from aiogram.filters import Command

logger = logging.getLogger(__name__)
widget_router = Router()

# Widget HTML ni bir marta o'qib olamiz
with open("widget/dice_duel.html", "r", encoding="utf-8") as f:
    WIDGET_HTML = f.read()

# Aktiv o'yinlar: {widget_message_id: game_state}
active_games: dict[int, dict] = {}


# ─── /duel — widget yuborish ──────────────────────────────────────────
@widget_router.message(Command("duel"))
async def cmd_duel(message: Message, bot: Bot):
    user = message.from_user

    state = {
        "p1id":    user.id,
        "p1name":  user.first_name[:12],
        "p2name":  "Raqib",
        "p1roll":  None,
        "p2roll":  None,
        "myRolled": False,
        "p2rolled": False,
        "done":    False,
    }

    try:
        # sendWidget — Bot API 10.4 yangi metod
        result = await bot.send_widget(
            chat_id=message.chat.id,
            html=WIDGET_HTML,
            state=json.dumps(state),
        )
        active_games[result.message_id] = state
        logger.info(f"Widget yuborildi: message_id={result.message_id}")

    except Exception as e:
        # sendWidget hali to'liq production'da chiqmagan bo'lsa fallback
        logger.warning(f"sendWidget ishlamadi: {e}")
        await message.answer(
            "🎲 <b>Dice Duel</b> — Widget versiyasi\n\n"
            "⚠️ Widget hozircha test serverda mavjud.\n"
            "Hozircha oddiy o'yin:\n\n"
            f"🎲 Sizning zaringiz: <b>{random.randint(1,6)}</b>\n"
            f"🎲 Raqib zarini: <b>{random.randint(1,6)}</b>"
        )


# ─── Widget Query handler ──────────────────────────────────────────────
@widget_router.widget_query()
async def handle_widget_query(query, bot: Bot):
    """Foydalanuvchi widget ichida tugma bosganida chaqiriladi"""
    try:
        data = json.loads(query.data)
        action = data.get("action")
        msg_id = query.message.message_id
        game = active_games.get(msg_id)

        if not game or game["done"]:
            await query.answer("O'yin tugagan!")
            return

        if action == "roll":
            user_id = query.from_user.id
            roll_val = random.randint(1, 6)

            if user_id == game["p1id"] and not game["myRolled"]:
                game["p1roll"] = roll_val
                game["myRolled"] = True
            elif user_id != game["p1id"] and not game["p2rolled"]:
                # Raqib (ikkinchi o'yinchi)
                if not game.get("p2id"):
                    game["p2id"] = user_id
                    game["p2name"] = query.from_user.first_name[:12]
                game["p2roll"] = roll_val
                game["p2rolled"] = True
            else:
                await query.answer("Siz allaqachon zar otgansiz!")
                return

            # Ikkalasi ham otdimi?
            if game["myRolled"] and game["p2rolled"]:
                game["done"] = True

            # Widget state ni yangilash
            await bot.edit_message_widget_data(
                chat_id=query.message.chat.id,
                message_id=msg_id,
                state=json.dumps(game),
            )
            await query.answer(f"🎲 Zar: {roll_val}!")

    except Exception as e:
        logger.error(f"Widget query xatosi: {e}")
        await query.answer("Xato yuz berdi!")
