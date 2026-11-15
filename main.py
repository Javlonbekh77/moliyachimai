import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot import setup_bot
from services.notifier import run_weekly_digest, run_monthly_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    bot, dp = setup_bot()
    
    # 1. Delete webhook if any was active, so polling works smoothly
    logger.info("Dropping any existing webhook for polling mode...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 2. Setup background scheduler for weekly/monthly reminders
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    # Sunday at 20:00 Tashkent time
    scheduler.add_job(
        run_weekly_digest,
        trigger=CronTrigger(day_of_week="sun", hour=20, minute=0, timezone="Asia/Tashkent"),
        args=[bot],
        id="weekly_digest"
    )
    
    # Last day of month at 21:00 Tashkent time
    scheduler.add_job(
        run_monthly_digest,
        trigger=CronTrigger(day="last", hour=21, minute=0, timezone="Asia/Tashkent"),
        args=[bot],
        id="monthly_digest"
    )
    
    scheduler.start()
    logger.info("Scheduler started (Weekly: Sunday 20:00, Monthly: Last day 21:00 Tashkent time).")
    
    # 3. Start Polling
    bot_info = await bot.get_me()
    logger.info(f"Bot started successfully as @{bot_info.username} ({bot_info.first_name})!")
    print(f"\n==========================================")
    print(f"🚀 Botingiz ishga tushdi: @{bot_info.username}")
    print(f"👉 Telegramda botga /start yuboring!")
    print(f"==========================================\n")
    
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
