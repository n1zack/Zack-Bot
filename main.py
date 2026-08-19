import os
import logging
from pyrogram import Client
from aiohttp import web
import config
from database import init_db

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
init_db()

# إعداد البوت
app = Client(
    "SuperAdminBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# إعداد سيرفر الويب الذي يطلبه Render
async def handle(request):
    return web.Response(text="Bot is active!")

app_web = web.Application()
app_web.add_routes([web.get('/', handle)])

if __name__ == "__main__":
    # تشغيل البوت مع السيرفر باستخدام خاصية compose من pyrogram
    # هذه الطريقة هي الأكثر استقراراً على السيرفرات
    logging.info("Starting Bot and Web Server...")
    
    # تشغيل السيرفر على البورت 10000
    port = int(os.environ.get("PORT", 10000))
    
    # ربط البوت بالدورة التشغيلية
    app.start()
    web.run_app(app_web, host='0.0.0.0', port=port)
 
