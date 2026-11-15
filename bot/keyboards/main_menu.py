from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="📊 Bugungi hisob"),
            KeyboardButton(text="📅 Oylik hisobot")
        ],
        [
            KeyboardButton(text="📈 Statistika"),
            KeyboardButton(text="🧠 AI Tahlil & Maslahat")
        ],
        [
            KeyboardButton(text="↩️ Oxirgisini o'chirish"),
            KeyboardButton(text="ℹ️ Yordam")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_transaction_inline_kb(tx_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del:{tx_id}")
            ]
        ]
    )


def get_analysis_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💡 AI Moliyaviy maslahat", callback_data="btn_advice"),
                KeyboardButton if False else InlineKeyboardButton(text="📅 Oylik hisob", callback_data="btn_month")
            ]
        ]
    )
