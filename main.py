import asyncio
import os
import logging
import uvicorn
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot import setup_bot
from services.notifier import run_weekly_digest, run_monthly_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Koyeb va bulutli platformalar salomatlik tekshiruvi (Healthcheck) uchun
health_app = FastAPI()

@health_app.get("/")
@health_app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "Moliyachim AI Telegram Bot",
        "mode": "polling_daemon"
    }

async def start_bot():
    bot, dp = setup_bot()
    
    # 1. Oldingi webhook bo'lsa o'chirish (polling to'siqsiz ishlashi uchun)
    logger.info("Dropping any existing webhook for polling mode...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 2. Haftalik va oylik eslatmalar jadvali
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(
        run_weekly_digest,
        trigger=CronTrigger(day_of_week="sun", hour=20, minute=0, timezone="Asia/Tashkent"),
        args=[bot],
        id="weekly_digest"
    )
    scheduler.add_job(
        run_monthly_digest,
        trigger=CronTrigger(day="last", hour=21, minute=0, timezone="Asia/Tashkent"),
        args=[bot],
        id="monthly_digest"
    )
    scheduler.start()
    logger.info("Scheduler started (Weekly: Sunday 20:00, Monthly: Last day 21:00 Tashkent time).")
    
    # 3. Telegram bilan aloqa
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

async def main():
    port = int(os.getenv("PORT", 8000))
    config = uvicorn.Config(health_app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    
    # Bot polling va Health check serverni bir vaqtda parallel yurgizish
    bot_task = asyncio.create_task(start_bot())
    server_task = asyncio.create_task(server.serve())
    
    await asyncio.gather(bot_task, server_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
