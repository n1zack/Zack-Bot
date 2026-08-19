import asyncio
import logging
from pyrogram import Client, idle
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

# سيرفر ويب لإبقاء الخدمة نشطة على Render
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    # تشغيل سيرفر الويب
    web_app = web.Application()
    web_app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    
    # تشغيل البوت
    await app.start()
    logging.info("Bot started successfully!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
