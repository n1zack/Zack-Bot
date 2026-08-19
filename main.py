import asyncio
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

# سيرفر ويب وهمي لإرضاء Render فقط
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    web_app = web.Application()
    web_app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

async def main():
    await start_web_server()
    await app.start()
    print("Bot is started successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
