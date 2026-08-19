import asyncio
import sys

# حل مشكلة حلقة الأحداث في بايثون الحديثة لـ Pyrogram
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import logging
from pyrogram import Client
from aiohttp import web
import config
from database import init_db

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)

# تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

app = Client(
    "SuperAdminBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web():
    web_app = web.Application()
    web_app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web())
    
    logging.info("Starting Telegram Bot...")
    app.run()
