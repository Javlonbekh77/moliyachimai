import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Header, HTTPException, status
from aiogram.types import Update
from config import settings
from bot import setup_bot
from services.notifier import run_weekly_digest, run_monthly_digest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot, dp = setup_bot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Webhook mode setup if webhook_url configured
    if settings.webhook_url:
        webhook_path = f"{settings.webhook_url.rstrip('/')}/api/webhook"
        logger.info(f"Setting Telegram webhook to: {webhook_path}")
        await bot.set_webhook(
            url=webhook_path,
            secret_token=settings.webhook_secret,
            drop_pending_updates=True
        )
    yield
    # Cleanup
    await bot.session.close()

app = FastAPI(title="Moliyachim AI API", lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": "Moliyachim AI Telegram Bot",
        "version": "1.0.0"
    }

@app.post("/api/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    # Verify webhook secret if configured
    if settings.webhook_secret and x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token"
        )
        
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/api/cron/weekly")
async def cron_weekly(auth: str = Header(None)):
    """
    Called by Vercel Cron every Sunday.
    """
    await run_weekly_digest(bot)
    return {"status": "Weekly digest sent"}

@app.get("/api/cron/monthly")
async def cron_monthly(auth: str = Header(None)):
    """
    Called by Vercel Cron on the last day of each month.
    """
    await run_monthly_digest(bot)
    return {"status": "Monthly digest sent"}

@app.get("/api/set_webhook")
async def set_webhook_manual(url: str):
    """
    Helper endpoint to set webhook URL dynamically.
    """
    webhook_url = f"{url.rstrip('/')}/api/webhook"
    res = await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.webhook_secret,
        drop_pending_updates=True
    )
    return {"webhook_url": webhook_url, "result": res}
