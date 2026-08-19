import asyncio
import sys

# إنشاء حلقة أحداث مسبقة لتجنب خطأ Pyrogram مع Python 3.14
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import os
import logging
from aiohttp import web
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

if __name__ == "__main__":
    # استيراد وتشكيل عميل Pyrogram بعد تثبيت حلقة الأحداث
    from pyrogram import Client
    
    app = Client(
        "SuperAdminBot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN
    )
    
    logging.info("Starting Telegram Bot & Web Server...")
    
    # تشغيل البوت بطريقة غير متزامنة لتجنب تعارض الـ Threads
    app.start()
    
    # تشغيل سيرفر الويب على المنفذ المطلوب
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app_web, host='0.0.0.0', port=port, print=None)
 
