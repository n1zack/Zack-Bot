import asyncio
import sys

# إنشاء حلقة أحداث مسبقة وإجبار بايثون عليها لتتوافق مع Pyrogram تماماً
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import threading
import logging
from pyrogram import Client
from aiohttp import web
from aiohttp.web import Response
import config
from database import init_db

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)

# تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

# إنشاء عميل البوت
app = Client(
    "SuperAdminBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# إعداد سيرفر الويب الوهمي لإرضاء Render
web_app = web.Application()
async def handle(request):
    return Response(text="Bot is running and active!")

web_app.add_routes([web.get('/', handle)])

def run_web_server():
    web.run_app(web_app, host='0.0.0.0', port=10000, print=None)

if __name__ == "__main__":
    # تشغيل سيرفر الويب في خلفية منفصلة
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logging.info("Web server started in background.")

    # تشغيل بوت تيليجرام
    logging.info("Starting Telegram Bot...")
    app.run()
