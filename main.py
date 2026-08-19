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
    # تشغيل سيرفر الويب على المنفذ 10000 بشكل منفصل
    web.run_app(web_app, host='0.0.0.0', port=10000, print=None)

if __name__ == "__main__":
    # تشغيل سيرفر الويب في خلفية منفصلة (Thread)
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    logging.info("Web server started in background.")

    # تشغيل بوت تيليجرام بشكل أساسي
    logging.info("Starting Telegram Bot...")
    app.run()
