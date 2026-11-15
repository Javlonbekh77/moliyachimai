import logging
from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from services.groq_service import parse_text_transactions, generate_financial_analysis
from services.db_service import (
    add_transactions_batch,
    get_today_transactions,
    get_month_transactions,
    calculate_stats
)
from bot.keyboards.main_menu import get_transaction_inline_kb, get_main_keyboard
from bot.handlers.commands import (
    handle_today,
    handle_month,
    handle_stats,
    handle_analyze_cmd,
    handle_delete_last,
    handle_help
)

logger = logging.getLogger(__name__)
router = Router()

def format_number(val: float) -> str:
    return f"{val:,.0f}".replace(",", " ")

@router.message(F.text)
async def handle_text_message(message: Message, bot: Bot):
    text = message.text.strip()
    
    # 1. Check if user clicked menu buttons
    if text == "📊 Bugungi hisob":
        return await handle_today(message)
    elif text == "📅 Oylik hisobot":
        return await handle_month(message)
    elif text == "📈 Statistika":
        return await handle_stats(message)
    elif text == "🧠 AI Tahlil & Maslahat":
        return await handle_analyze_cmd(message)
    elif text == "↩️ Oxirgisini o'chirish":
        return await handle_delete_last(message)
    elif text == "ℹ️ Yordam":
        return await handle_help(message)
        
    user = message.from_user
    user_id = user.id
    
    # 2. Tezkor javob (instant acknowledgement)
    status_msg = await message.answer("✍️ <i>Tahlil qilinmoqda...</i>")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    # 3. Parse text with Groq LLM
    try:
        result = await parse_text_transactions(text)
        
        # If it's a question, advice inquiry, or general discussion
        if result.is_query or not result.transactions:
            txs = get_month_transactions(user_id)
            stats = calculate_stats(txs)
            
            analysis = await generate_financial_analysis(
                user_name=user.first_name,
                stats=stats,
                recent_transactions=txs,
                user_query=text
            )
            await status_msg.edit_text(f"🧠 <b>AI Moliyaviy Maslahatchi:</b>\n\n{analysis}", reply_markup=get_main_keyboard())
            return
            
        # 4. If transactions found, save to Firestore
        saved_txs = add_transactions_batch(
            user_id=user_id,
            items=result.transactions,
            raw_input=text,
            input_type="text"
        )
        
        lines = []
        last_id = saved_txs[0]["id"] if saved_txs else ""
        
        for tx in saved_txs:
            t_type = tx.get("type")
            amt = tx.get("amount", 0)
            cur = tx.get("currency", "UZS")
            cat = tx.get("category", "Boshqa")
            desc = tx.get("description", "")
            
            if t_type == "expense":
                lines.append(f"🔴 <b>{cat}:</b> -{format_number(amt)} {cur} <i>({desc})</i>")
            else:
                lines.append(f"🟢 <b>{cat}:</b> +{format_number(amt)} {cur} <i>({desc})</i>")
                
        reply_text = (
            f"✅ <b>Kiritildi va saqlandi:</b>\n\n"
            + "\n".join(lines) + "\n\n"
            f"<i>Xatolik bo'lsa, quyidagi tugma orqali bekor qilishingiz mumkin:</i>"
        )
        
        await status_msg.edit_text(
            reply_text,
            reply_markup=get_transaction_inline_kb(last_id)
        )
        
    except Exception as e:
        logger.error(f"Text processing error: {e}", exc_info=True)
        try:
            await status_msg.edit_text(
                "😔 Xabarni qayta ishlashda xatolik yuz berdi. Iltimos, qaytadan yozib ko'ring yoki /help ni bosing.",
                reply_markup=get_main_keyboard()
            )
        except Exception:
            await message.answer("😔 Xabarni qayta ishlashda xatolik yuz berdi.")
