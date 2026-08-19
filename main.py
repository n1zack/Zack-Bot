import asyncio
import sys

# ضمان توافق حلقة الأحداث مع بايثون الحديثة
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import os
import threading
import logging
from aiohttp import web
from pyrogram import Client
import config
from database import init_db

# إعداد التسجيل وقاعدة البيانات
logging.basicConfig(level=logging.INFO)
init_db()

# إعداد سيرفر الويب لـ Render
async def handle(request):
    return web.Response(text="Bot is running and active!")

app_web = web.Application()
app_web.add_routes([web.get('/', handle)])

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app_web, host='0.0.0.0', port=port, print=None)

if __name__ == "__main__":
    # 1. تشغيل سيرفر الويب في الخلفية ليبقى المنفذ مفتوحاً دائماً أمام Render
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logging.info("Web server started successfully in background.")

    # 2. تشغيل عميل بوت تيليجرام ليعمل بشكل أساسي ومستمر
    logging.info("Starting Telegram Bot...")
    app = Client(
        "SuperAdminBot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN
    )
    
    # تشغيل البوت
    app.run()
