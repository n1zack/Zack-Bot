import os
import asyncio
import threading
import logging
from aiohttp import web
import config
from database import init_db

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
init_db()

# إعداد سيرفر الويب لـ Render
async def handle(request):
    return web.Response(text="Zack-Bot is running successfully!")

web_app = web.Application()
web_app.add_routes([web.get('/', handle)])

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web.run_app(web_app, host='0.0.0.0', port=port, print=None)

if __name__ == "__main__":
    # تشغيل سيرفر الويب في الخلفية ليظل البورت مفتوحاً
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logging.info("Web server started in background.")

    # تأخير استيراد وبدء البوت لحين ضمان جاهزية البيئة
    import pyrogram
    from pyrogram import Client

    logging.info("Starting Telegram Bot...")
    app = Client(
        "SuperAdminBot",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        bot_token=config.BOT_TOKEN
    )
    
    app.run()
