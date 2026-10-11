import asyncio
import os

from pyrogram import Client, idle
from pyrogram.types import BotCommand

from config import (
    TEL_API_ID,
    TEL_API_HASH,
    TEL_BOT_TOKEN,
    ADMIN_IDS,
    TELPROXY,
)
from db.db_async import checkpoint_db
from db.model_async import create_tables, add_user, set_admin
from db.redis_client import close_redis
from services.bale_service import bale_bot
from utils.logger import get_logger, setup_logger

logger = get_logger(__name__)

plugins = dict(root="handlers")

telapp = Client(
    "bot",
    api_id=TEL_API_ID,
    api_hash=TEL_API_HASH,
    bot_token=TEL_BOT_TOKEN,
    plugins=plugins,
    proxy=TELPROXY,
)


async def setup_bot_commands():
    await telapp.set_bot_commands([
        BotCommand("start", "شروع ربات"),
        BotCommand("help", "راهنمای استفاده از ربات"),
    ])


async def main():
    setup_logger()
    await create_tables()
    for admin_id in ADMIN_IDS:
        await add_user(admin_id, is_admin=True)
        await set_admin(admin_id)
    await telapp.start()
    await setup_bot_commands()

    max_runtime_minutes = int(os.getenv("MAX_RUNTIME_MINUTES", "0"))
    if max_runtime_minutes > 0:
        logger.info(
            f"GitHub Actions mode active: Bot running with {max_runtime_minutes} minutes rotation timer."
        )
        try:
            await asyncio.wait_for(idle(), timeout=max_runtime_minutes * 60)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            logger.info("Rotation timer elapsed. Initiating graceful shutdown for next handover...")
    else:
        await idle()

    await telapp.stop()
    await bale_bot.close()
    await close_redis()
    await checkpoint_db()
    logger.info("Bot shutdown completed cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
