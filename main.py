import os
import asyncio
import logging
from aiohttp import web
from pyrogram import Client
import config
from database import init_db

# إعداد التسجيل وقاعدة البيانات
logging.basicConfig(level=logging.INFO)
init_db()

# إعداد البوت
app = Client(
    "SuperAdminBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# سيرفر الويب المطلوب من Render
async def handle(request):
    return web.Response(text="Zack-Bot is running successfully!")

web_app = web.Application()
web_app.add_routes([web.get('/', handle)])

async def main():
    # بدء تشغيل البوت بشكل غير متزامن
    await app.start()
    logging.info("Telegram Bot started successfully.")
    
    # إعداد وبدء سيرفر الويب على المنفذ المطلوب من Render
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}.")

if __name__ == "__main__":
    # تشغيل حلقة الأحداث الأساسية
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
