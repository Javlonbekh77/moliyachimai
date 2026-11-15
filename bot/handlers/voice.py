import io
import logging
from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from services.gemini_service import process_voice_audio
from services.db_service import (
    add_transactions_batch,
    get_month_transactions,
    calculate_stats
)
from services.groq_service import generate_financial_analysis
from bot.keyboards.main_menu import get_transaction_inline_kb, get_main_keyboard

logger = logging.getLogger(__name__)
router = Router()

def format_number(val: float) -> str:
    return f"{val:,.0f}".replace(",", " ")

@router.message(F.voice)
async def handle_voice_message(message: Message, bot: Bot):
    user = message.from_user
    user_id = user.id
    
    # 1. Tezkor javob (instant acknowledgement)
    status_msg = await message.answer("🎧 <i>Eshityapman...</i>")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
    
    try:
        # Download voice file into memory buffer
        voice_file = await bot.get_file(message.voice.file_id)
        voice_buffer = io.BytesIO()
        await bot.download_file(voice_file.file_path, destination=voice_buffer)
        audio_bytes = voice_buffer.getvalue()
        
        # Multimodal AI processing directly with Google Gemini
        result = await process_voice_audio(audio_bytes, mime_type="audio/ogg")
        
        # If user asked a question or financial advice in voice
        if result.is_query or not result.transactions:
            txs = get_month_transactions(user_id)
            stats = calculate_stats(txs)
            analysis = await generate_financial_analysis(
                user_name=user.first_name,
                stats=stats,
                recent_transactions=txs,
                user_query="Foydalanuvchi ovozli xabar orqali savol yoki moliyaviy maslahat so'radi."
            )
            await status_msg.edit_text(f"🧠 <b>AI Moliyaviy Javobi:</b>\n\n{analysis}", reply_markup=get_main_keyboard())
            return
            
        # If transactions found, save to Firestore in batch
        saved_txs = add_transactions_batch(
            user_id=user_id,
            items=result.transactions,
            raw_input="[Ovozli xabar]",
            input_type="voice"
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
            f"✅ <b>Ovozli xabar orqali saqlandi:</b>\n\n"
            + "\n".join(lines) + "\n\n"
            f"<i>Xato eshitilgan bo'lsa, quyidagi tugma orqali bekor qilishingiz mumkin:</i>"
        )
        
        await status_msg.edit_text(
            reply_text,
            reply_markup=get_transaction_inline_kb(last_id)
        )
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}", exc_info=True)
        try:
            await status_msg.edit_text(
                "😔 Ovozli xabarni tushunishda xatolik yuz berdi. Iltimos, qaytadan aniqroq gapiring yoki matn ko'rinishida yozing.",
                reply_markup=get_main_keyboard()
            )
        except Exception:
            await message.answer("😔 Ovozli xabarni tushunishda xatolik yuz berdi.")
