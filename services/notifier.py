import logging
from datetime import datetime
from aiogram import Bot
from services.db_service import (
    get_all_active_users,
    get_week_transactions,
    get_month_transactions,
    calculate_stats,
    get_current_time
)
from services.groq_service import generate_financial_analysis

logger = logging.getLogger(__name__)

async def run_weekly_digest(bot: Bot):
    """
    Called every Sunday evening.
    Sends engaging weekly analysis and hooks to all active users.
    """
    logger.info("Starting Sunday Weekly Digest...")
    users = get_all_active_users()
    
    for u in users:
        user_id = u.get("user_id")
        first_name = u.get("first_name", "Do'stim")
        if not user_id:
            continue
            
        try:
            txs = get_week_transactions(user_id)
            if not txs:
                # Inactive hook
                text = (
                    f"👀 <b>{first_name}, bu hafta nima gap? Qayerlardasiz?</b>\n\n"
                    f"Birorta ham xarajat yoki daromad kiritmabsiz-ku! Nega pul qo'shmayapsiz? 😉\n\n"
                    f"<i>Balki pullarni yostiq ostida yashirib qo'ygandirsiz yoki shunchaki yozish yoddan chiqdimi?</i>\n\n"
                    f"🎙 Keling, haftalik xarajatlaringizni 10 soniyalik ovozli xabar qilib yuboring, bir zumda hisoblab beraman!"
                )
            else:
                stats = calculate_stats(txs)
                total_exp = stats["total_expense"]
                total_inc = stats["total_income"]
                balance = stats["balance"]
                top_cat = stats["top_category"] or "Mavjud emas"
                
                text = (
                    f"📊 <b>Yakshanba oqshomi — haftalik sarhisob vaqti, {first_name}!</b>\n\n"
                    f"Qani, bu hafta cho'ntagingiz qanday 'harakatlanganini' ko'raylikchi: 👇\n\n"
                    f"🟢 <b>Daromad:</b> {total_inc:,.0f} UZS\n"
                    f"🔴 <b>Xarajat:</b> {total_exp:,.0f} UZS\n"
                    f"⚖️ <b>Sof qoldiq:</b> {balance:,.0f} UZS\n"
                    f"🏆 <b>Eng katta xarajat toifasi:</b> {top_cat}\n\n"
                    f"🔍 <i>To'liq tahlil va tejash bo'yicha maslahat olish uchun menga istalgan savolingizni yozing yoki pastdagi <b>🧠 AI Tahlil & Maslahat</b> tugmasini bosing!</i>"
                )
                
            await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error sending weekly digest to {user_id}: {e}")


async def run_monthly_digest(bot: Bot):
    """
    Called on the last day of each month.
    Sends monthly wrap-up and strategic financial analysis.
    """
    logger.info("Starting Monthly Digest...")
    users = get_all_active_users()
    now = get_current_time()
    month_name = now.strftime("%B")
    
    for u in users:
        user_id = u.get("user_id")
        first_name = u.get("first_name", "Do'stim")
        if not user_id:
            continue
            
        try:
            txs = get_month_transactions(user_id)
            if not txs:
                text = (
                    f"🎯 <b>{first_name}, oy yakunlandi!</b>\n\n"
                    f"Lekin bu oy hech qanday xarajat kiritmadingiz. Nega pul qo'shmayapsiz? 🤔\n"
                    f"Yangi oyni toza va aniq hisob-kitob bilan boshlashga nima deysiz? Bugundanoq har bir xarajatni menga ovoz bilan aytib turing!"
                )
            else:
                stats = calculate_stats(txs)
                total_exp = stats["total_expense"]
                total_inc = stats["total_income"]
                balance = stats["balance"]
                
                cat_lines = []
                for cat, amt in stats["categories"][:5]:
                    pct = (amt / total_exp * 100) if total_exp > 0 else 0
                    cat_lines.append(f"  • {cat}: <b>{amt:,.0f} UZS</b> ({pct:.1f}%)")
                    
                cats_str = "\n".join(cat_lines) if cat_lines else "  • Xarajatlar yo'q"
                
                text = (
                    f"🎯 <b>Oy yakunlandi! Keling, bu oy cho'ntagingiz qanday 'nafas olgani'ni ko'ramiz! 🚀</b>\n\n"
                    f"👤 <b>Foydalanuvchi:</b> {first_name}\n"
                    f"📅 <b>Davr:</b> Shu oy\n\n"
                    f"💰 <b>Jami daromad:</b> {total_inc:,.0f} UZS\n"
                    f"💸 <b>Jami xarajat:</b> {total_exp:,.0f} UZS\n"
                    f"💼 <b>Qolgan mablag':</b> {balance:,.0f} UZS\n\n"
                    f"<b>Asosiy xarajat yo'nalishlari:</b>\n{cats_str}\n\n"
                    f"💡 <i>Keyingi oyda ko'proq jamg'arma qilish uchun budjet tuzamizmi? Istalgan savolingizni yozing, birga tahlil qilamiz!</i>"
                )
                
            await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error sending monthly digest to {user_id}: {e}")
