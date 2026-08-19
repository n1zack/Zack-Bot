import os
import logging
from aiohttp import web
import config
from database import init_db
from pyrogram import Client

# إعداد التسجيل وقاعدة البيانات
logging.basicConfig(level=logging.INFO)
init_db()

# إعداد سيرفر الويب البسيط جداً (بدون إشارات معقدة)
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

# إعداد البوت
app = Client(
    "SuperAdminBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

@app.on_message()
async def start_handler(client, message):
    if message.text == "/start":
        await message.reply("أهلاً بك يا زاك! البوت يعمل بكامل طاقتة.")

if __name__ == "__main__":
    # تشغيل سيرفر الويب بالتزامن مع تشغيل البوت في نفس الحلقة الأساسية
    loop = app.loop
    loop.run_until_complete(start_web_server())
    
    logging.info("Starting Telegram Bot...")
    app.run()
