import os
import logging
from aiohttp import web
from pyrogram import Client
from database import init_db

# إعداد التسجيل وقاعدة البيانات
logging.basicConfig(level=logging.INFO)
init_db()

# بيانات البوت مباشرة هنا لضمان عدم حدوث أي خطأ
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
ADMIN_ID = 1251313339

# إعداد سيرفر الويب لـ Render
async def handle(request):
    return web.Response(text="Zack-Bot is running successfully!")

app_web = web.Application()
app_web.add_routes([web.get('/', handle)])

async def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}.")

# إعداد بوت تيليجرام
app = Client(
    "SuperAdminBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

if __name__ == "__main__":
    # تشغيل سيرفر الويب بالتزامن مع البوت
    loop = app.loop
    loop.run_until_complete(start_web_server())
    
    logging.info("Starting Telegram Bot...")
    app.run()
