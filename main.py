import os
import logging
from aiohttp import web
from telethon import TelegramClient, events
from database import init_db

logging.basicConfig(level=logging.INFO)
init_db()

# بياناتك مباشرة
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'

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

# إعداد البوت باستخدام Telethon
client = TelegramClient('zack_bot', API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('أهلاً بك يا زاك! البوت يعمل بكامل طاقته.')

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Telegram Bot started successfully.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
 
