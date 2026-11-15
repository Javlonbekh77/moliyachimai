import logging
from bot.instance import bot, dp
from bot.handlers import commands, voice, text
from bot.middlewares.auth import UserRegistrationMiddleware

logger = logging.getLogger(__name__)

def setup_bot():
    # Register middlewares
    dp.message.middleware(UserRegistrationMiddleware())
    dp.callback_query.middleware(UserRegistrationMiddleware())

    # Register routers (order: commands -> voice -> text)
    dp.include_router(commands.router)
    dp.include_router(voice.router)
    dp.include_router(text.router)
    
    logger.info("Bot handlers and middlewares successfully registered.")
    return bot, dp
