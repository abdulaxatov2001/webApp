from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import os
import json
import random

load_dotenv()

router = Router()
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")

# ─── Puzzle ma'lumotlari ───────────────────────────────────────────────
PUZZLES = [
    {
        "id": 1,
        "question": "🔢 Men 2 xonali sonman. O'nlar raqamim birlar raqamimdan 3 ta ko'p. Yig'indim 11. Men kimman?",
        "answer": "74",
        "hint": "O'nlar + birlar = 11, o'nlar - birlar = 3",
        "options": ["47", "74", "83", "56"]
    },
    {
        "id": 2,
        "question": "🧩 Bir fermer 17 ta qo'yi bor edi. Bittasidan tashqari hammasi o'lib qoldi. Qancha qo'y qoldi?",
        "answer": "17",
        "hint": "Savolni diqqat bilan o'qi 😉",
        "options": ["1", "16", "17", "0"]
    },
    {
        "id": 3,
        "question": "🔢 1, 1, 2, 3, 5, 8, 13, ... keyingi son?",
        "answer": "21",
        "hint": "Fibonacci ketma-ketligi",
        "options": ["18", "20", "21", "25"]
    },
    {
        "id": 4,
        "question": "⚖️ 1 kg paxta og'irroqmi yoki 1 kg temirmi?",
        "answer": "Teng",
        "hint": "Ikkalasi ham 1 kg 😄",
        "options": ["Paxta", "Temir", "Teng", "Bilmayman"]
    },
    {
        "id": 5,
        "question": "🧮 Agar 5 ta mushuk 5 daqiqada 5 ta sichqon tutsa, 100 ta mushuk 100 daqiqada nechta sichqon tutadi?",
        "answer": "10000",
        "hint": "Har bir mushuk 1 daqiqada 1 ta tutadi",
        "options": ["100", "500", "1000", "10000"]
    },
]

# Foydalanuvchilar holati (xotirada saqlash)
user_states: dict[int, dict] = {}


# ─── /start ───────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 O'yinni boshlash", callback_data="start_game")
    kb.button(text="🏆 Reyting", callback_data="leaderboard")
    kb.button(text="📱 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
    kb.adjust(2, 1)

    await message.answer(
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        "🧩 <b>Puzzle Bot</b>ga xush kelibsiz!\n\n"
        "🎯 Bu yerda mantiqiy va raqamli topishmoqlarni yechasiz.\n"
        "✅ To'g'ri javob = +10 ball\n"
        "💡 Hint = -3 ball\n"
        "❌ Noto'g'ri javob = -2 ball\n\n"
        "Tayyor bo'lsangiz, boshlang! 👇",
        reply_markup=kb.as_markup()
    )


# ─── O'yinni boshlash ─────────────────────────────────────────────────
@router.callback_query(F.data == "start_game")
async def start_game(call: CallbackQuery):
    user_id = call.from_user.id
    puzzle = random.choice(PUZZLES)

    user_states[user_id] = {
        "puzzle_id": puzzle["id"],
        "score": user_states.get(user_id, {}).get("score", 0),
        "total": user_states.get(user_id, {}).get("total", 0),
        "hint_used": False,
    }

    await send_puzzle(call.message, puzzle, user_id)
    await call.answer()


async def send_puzzle(message: Message, puzzle: dict, user_id: int):
    kb = InlineKeyboardBuilder()
    for option in puzzle["options"]:
        kb.button(
            text=option,
            callback_data=f"answer:{puzzle['id']}:{option}"
        )
    kb.button(text="💡 Hint (-3 ball)", callback_data=f"hint:{puzzle['id']}")
    kb.button(text="⏭ Keyingi savol", callback_data="start_game")
    kb.adjust(2, 2, 1)

    state = user_states.get(user_id, {})
    score = state.get("score", 0)
    total = state.get("total", 0)

    await message.edit_text(
        f"🧩 <b>Topishmoq #{puzzle['id']}</b>\n\n"
        f"{puzzle['question']}\n\n"
        f"📊 Ball: <b>{score}</b> | Jami: <b>{total}</b> ta yechildi",
        reply_markup=kb.as_markup()
    )


# ─── Javob berish ─────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("answer:"))
async def check_answer(call: CallbackQuery):
    _, puzzle_id, selected = call.data.split(":", 2)
    puzzle_id = int(puzzle_id)
    user_id = call.from_user.id

    puzzle = next((p for p in PUZZLES if p["id"] == puzzle_id), None)
    if not puzzle:
        await call.answer("Topishmoq topilmadi!", show_alert=True)
        return

    state = user_states.setdefault(user_id, {"score": 0, "total": 0, "hint_used": False})
    is_correct = selected.strip() == puzzle["answer"].strip()

    if is_correct:
        state["score"] += 10
        state["total"] += 1
        emoji = "✅"
        result_text = f"To'g'ri! +10 ball 🎉"
    else:
        state["score"] -= 2
        emoji = "❌"
        result_text = f"Noto'g'ri! -2 ball\nTo'g'ri javob: <b>{puzzle['answer']}</b>"

    state["hint_used"] = False

    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 Keyingi savol", callback_data="start_game")
    kb.button(text="🏆 Reyting", callback_data="leaderboard")
    kb.adjust(2)

    await call.message.edit_text(
        f"{emoji} <b>{result_text}</b>\n\n"
        f"📊 Umumiy ball: <b>{state['score']}</b>\n"
        f"✅ Yechilgan: <b>{state['total']}</b> ta\n\n"
        f"Davom etasizmi?",
        reply_markup=kb.as_markup()
    )
    await call.answer(result_text[:200])


# ─── Hint ─────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("hint:"))
async def show_hint(call: CallbackQuery):
    _, puzzle_id = call.data.split(":", 1)
    puzzle_id = int(puzzle_id)
    user_id = call.from_user.id

    puzzle = next((p for p in PUZZLES if p["id"] == puzzle_id), None)
    if not puzzle:
        await call.answer("Topishmoq topilmadi!", show_alert=True)
        return

    state = user_states.setdefault(user_id, {"score": 0, "total": 0, "hint_used": False})

    if state.get("hint_used"):
        await call.answer("💡 Hint allaqachon ishlatilgan!", show_alert=True)
        return

    state["hint_used"] = True
    state["score"] -= 3

    await call.answer(
        f"💡 Hint: {puzzle['hint']}\n(-3 ball)",
        show_alert=True
    )


# ─── Leaderboard ──────────────────────────────────────────────────────
@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(call: CallbackQuery):
    user_id = call.from_user.id
    state = user_states.get(user_id, {"score": 0, "total": 0})

    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 O'yinni davom ettirish", callback_data="start_game")

    await call.message.edit_text(
        f"🏆 <b>Sizning natijangiz</b>\n\n"
        f"👤 Foydalanuvchi: <b>{call.from_user.first_name}</b>\n"
        f"⭐ Ball: <b>{state.get('score', 0)}</b>\n"
        f"✅ Yechilgan: <b>{state.get('total', 0)}</b> ta topishmoq\n\n"
        f"💪 Davom eting va ko'proq ball to'plang!",
        reply_markup=kb.as_markup()
    )
    await call.answer()


# ─── /help ────────────────────────────────────────────────────────────
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Qo'llanma</b>\n\n"
        "/start — Botni boshlash\n"
        "/help — Yordam\n\n"
        "🎮 <b>O'yin qoidalari:</b>\n"
        "• To'g'ri javob: +10 ball\n"
        "• Hint ishlatish: -3 ball\n"
        "• Noto'g'ri javob: -2 ball\n\n"
        "🧩 Qanchalik ko'p yechsangiz, shunchalik yaxshi!"
    )

