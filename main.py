import os
import logging
import zipfile
import asyncio
from aiohttp import web
from telethon import TelegramClient, events, Button
from database import init_db
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

logging.basicConfig(level=logging.INFO)
init_db()

API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'

# سيرفر الويب لـ Render
async def handle(request):
    return web.Response(text="Zack-Bot is running!")

app_web = web.Application()
app_web.add_routes([web.get('/', handle)])

async def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

client = TelegramClient('zack_bot', API_ID, API_HASH)

# --- معالجة الملفات (دعم الجلسات المتعددة) ---
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    path = await event.download_media()
    await event.respond("📂 جاري معالجة الملف...")
    
    count = 0
    # إذا كان الملف مضغوطاً
    if path.endswith('.zip'):
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall("temp_sessions")
            for file in os.listdir("temp_sessions"):
                if file.endswith('.session'):
                    # هنا تضع منطقك لإضافة الجلسة لقاعدة البيانات
                    count += 1
        await event.respond(f"✅ تم العثور على {count} جلسة وإضافتها بنجاح!")
    
    # إذا كان ملف session مباشرة
    elif path.endswith('.session'):
        await event.respond("✅ تم إضافة الجلسة بنجاح!")
    
    os.remove(path) # حذف الملف بعد المعالجة

# --- معالج الأزرار ---
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    
    if data == "my_numbers":
        await event.edit("📱 **أرقامك المسجلة:**\nلا توجد أرقام، استخدم 'إضافة رقم'.", buttons=get_back_keyboard())
    
    elif data == "session_login":
        await event.edit("📂 **أرسل ملف الجلسة الآن:**\nيمكنك إرسال ملف .session واحد أو ملف .zip يحتوي على عدة جلسات.", buttons=get_back_keyboard())
    
    elif data == "create_session":
        await event.edit("📁 **جاري ضغط جميع الجلسات الخاصة بك...**", buttons=get_back_keyboard())
        # هنا أضف كود ضغط المجلد الذي تخزن فيه الجلسات وإرساله كـ zip
    
    elif data == "back_home":
        await event.edit("👑 **مرحباً بك من جديد**", buttons=get_main_keyboard())
    
    # ... (باقي الأزرار كما هي في كودك)
    else:
        await event.answer("قيد التطوير", alert=True)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("👑 **مرحباً بك في لوحة تحكم البوت**", buttons=get_main_keyboard())

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
