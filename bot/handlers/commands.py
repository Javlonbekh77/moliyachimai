import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from services.db_service import (
    get_or_create_user,
    get_today_transactions,
    get_month_transactions,
    calculate_stats,
    delete_last_transaction,
    delete_transaction_by_id
)
from services.groq_service import generate_financial_analysis
from bot.keyboards.main_menu import get_main_keyboard, get_analysis_inline_kb

logger = logging.getLogger(__name__)
router = Router()

def format_number(val: float) -> str:
    return f"{val:,.0f}".replace(",", " ")

def make_progress_bar(percent: float, length: int = 10) -> str:
    filled = int(round(length * percent / 100))
    filled = min(max(filled, 0), length)
    return "🟩" * filled + "⬜" * (length - filled)


@router.message(CommandStart())
async def handle_start(message: Message):
    user = message.from_user
    get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>! 👋\n\n"
        f"Men sizning aqlli shaxsiy moliyaviy yordamchingiz — <b>Moliyachim AI</b> botiman.\n\n"
        f"<b>Mendan qanday foydalanish mumkin?</b>\n"
        f"🎙 <b>Ovozli xabar yuboring:</b>\n"
        f"<i>«Bugun tushlikka 45 ming ketdi, taksiga 15 ming berdim, oylikdan 2 million oldim»</i>\n\n"
        f"✍️ <b>Yoki oddiy matn yozing:</b>\n"
        f"<i>«non 5000, go'sht 120 ming, benzin 100 ming»</i>\n\n"
        f"🧠 <b>Moliyaviy maslahat oling:</b>\n"
        f"<i>«Xarajatlarimni tahlil qilib ber»</i> yoki <i>«Qanday qilib pul jamg'arsam bo'ladi?»</i>\n\n"
        f"Barcha xarajat va daromadlaringiz avtomatik hisoblab boriladi! 🚀"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(Command("help"))
async def handle_help(message: Message):
    help_text = (
        "ℹ️ <b>Moliyachim AI Buyruqlari va Imkoniyatlari:</b>\n\n"
        "• <b>Ovoz yoki matn yuborish:</b> Istalgan shaklda xarajat/daromadni ayting yoki yozing.\n"
        "• /today — Bugungi kun sarhisobi va kiritilgan operatsiyalar.\n"
        "• /month — Joriy oyning to'liq balansi va toifalar taqsimoti.\n"
        "• /stats — Grafiklar va batafsil tahliliy ko'rsatkichlar.\n"
        "• /analyze — AI tomonidan moliyaviy tahlil va ortiqcha xarajatlar auditi.\n"
        "• /advice — AI bilan interaktiv moliyaviy maslahat.\n"
        "• /delete_last — Oxirgi kiritilgan xatolikni darhol o'chirish.\n\n"
        "Har yakshanba oqshomida haftalik hisobot, har oy oxirida esa to'liq oylik sarhisob yuboriladi! 📊"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())


@router.message(Command("today"))
async def handle_today(message: Message):
    user_id = message.from_user.id
    txs = get_today_transactions(user_id)
    
    if not txs:
        await message.answer(
            "📊 <b>Bugun hali hech qanday xarajat yoki daromad kiritilmadi.</b>\n\n"
            "Ovozli yoki matnli xabar yuboring, darhol qo'shib qo'yaman! 😉",
            reply_markup=get_main_keyboard()
        )
        return
        
    stats = calculate_stats(txs)
    
    lines = []
    for tx in txs:
        icon = "🔴" if tx.get("type") == "expense" else "🟢"
        lines.append(
            f"{icon} <b>{tx.get('category')}</b>: {format_number(tx.get('amount', 0))} {tx.get('currency')} "
            f"<i>({tx.get('description')})</i>"
        )
        
    summary_text = (
        f"📅 <b>Bugungi hisob-kitobingiz:</b>\n\n"
        + "\n".join(lines) + "\n\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🟢 <b>Kirim (Daromad):</b> {format_number(stats['total_income'])} UZS\n"
        f"🔴 <b>Chiqim (Xarajat):</b> {format_number(stats['total_expense'])} UZS\n"
        f"⚖️ <b>Bugungi qoldiq:</b> {format_number(stats['balance'])} UZS"
    )
    await message.answer(summary_text, reply_markup=get_main_keyboard())


@router.message(Command("month"))
async def handle_month(message: Message):
    user_id = message.from_user.id
    txs = get_month_transactions(user_id)
    
    if not txs:
        await message.answer(
            "📅 <b>Shu oyda hali xarajatlar qayd etilmagan.</b>\n"
            "Xarajatlaringizni yuborishni boshlang!",
            reply_markup=get_main_keyboard()
        )
        return
        
    stats = calculate_stats(txs)
    total_exp = stats["total_expense"]
    
    cat_lines = []
    for cat, amt in stats["categories"]:
        pct = (amt / total_exp * 100) if total_exp > 0 else 0
        bar = make_progress_bar(pct, length=8)
        cat_lines.append(
            f"<b>{cat}</b>: {format_number(amt)} UZS ({pct:.1f}%)\n{bar}"
        )
        
    text = (
        f"📅 <b>Joriy oy sarhisobi:</b>\n\n"
        f"🟢 <b>Jami daromad:</b> {format_number(stats['total_income'])} UZS\n"
        f"🔴 <b>Jami xarajat:</b> {format_number(stats['total_expense'])} UZS\n"
        f"💼 <b>Sof jamg'arma:</b> {format_number(stats['balance'])} UZS\n\n"
        f"<b>Xarajatlarning taqsimoti:</b>\n"
        + ("\n\n".join(cat_lines) if cat_lines else "Xarajat yo'q")
    )
    await message.answer(text, reply_markup=get_analysis_inline_kb())


@router.message(Command("stats"))
async def handle_stats(message: Message):
    await handle_month(message)


@router.message(Command("analyze"))
@router.message(Command("advice"))
async def handle_analyze_cmd(message: Message):
    user_id = message.from_user.id
    user = message.from_user
    
    status_msg = await message.answer("⏳ <i>Moliya tahlilchilari hisob-kitobni boshladi...</i>")
    
    txs = get_month_transactions(user_id)
    stats = calculate_stats(txs)
    
    analysis = await generate_financial_analysis(
        user_name=user.first_name,
        stats=stats,
        recent_transactions=txs,
        user_query="Mening oylik sarf-xarajatlarimni chuqur tahlil qilib, qayerda ortiqcha xarajat qilayotganimni va tejash usullarini aytib ber."
    )
    
    await status_msg.delete()
    await message.answer(f"🧠 <b>AI Moliyaviy Tahlili:</b>\n\n{analysis}", reply_markup=get_main_keyboard())


@router.message(Command("delete_last"))
async def handle_delete_last(message: Message):
    user_id = message.from_user.id
    deleted = delete_last_transaction(user_id)
    
    if not deleted:
        await message.answer("❌ O'chirish uchun birorta ham operatsiya topilmadi.")
        return
        
    t_type = "Xarajat" if deleted.get("type") == "expense" else "Daromad"
    amt = format_number(deleted.get("amount", 0))
    desc = deleted.get("description", "")
    
    await message.answer(
        f"🗑 <b>Oxirgi operatsiya bekor qilindi va o'chirildi:</b>\n"
        f"{t_type}: {amt} {deleted.get('currency')} <i>({desc})</i>",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(F.data.startswith("del:"))
async def handle_delete_callback(callback: CallbackQuery):
    tx_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    success = delete_transaction_by_id(tx_id, user_id)
    
    if success:
        await callback.answer("✅ Operatsiya o'chirildi!", show_alert=False)
        try:
            await callback.message.edit_text(
                callback.message.html_text + "\n\n<i>[Ushbu yozuv o'chirib tashlandi] 🗑</i>",
                reply_markup=None
            )
        except Exception:
            pass
    else:
        await callback.answer("❌ O'chirib bo'lmadi yoki topilmadi.", show_alert=True)


@router.callback_query(F.data == "btn_advice")
async def handle_advice_callback(callback: CallbackQuery):
    await callback.answer()
    user = callback.from_user
    txs = get_month_transactions(user.id)
    stats = calculate_stats(txs)
    
    analysis = await generate_financial_analysis(
        user_name=user.first_name,
        stats=stats,
        recent_transactions=txs,
        user_query="Menga hozirgi moliyaviy holatimdan kelib chiqib, pul jamg'arish va oqilona sarflash bo'yicha amaliy 3 ta maslahat ber."
    )
    await callback.message.answer(f"💡 <b>Shaxsiy AI Maslahati:</b>\n\n{analysis}")


@router.callback_query(F.data == "btn_month")
async def handle_month_callback(callback: CallbackQuery):
    await callback.answer()
    await handle_month(callback.message)
