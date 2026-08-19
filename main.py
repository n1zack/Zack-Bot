import os
import logging
import zipfile
import asyncio
from aiohttp import web
from telethon import TelegramClient, events, Button
from telethon.tl.types import InputPeerEmpty
from database import init_db, add_user_number, get_user_numbers
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة قاعدة البيانات
init_db()

# بيانات الاتصال
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'
ADMIN_ID = 1251313339

# الحالة للمستخدمين
user_states = {}

# سيرفر الويب الخاص بـ Render
async def handle(request):
    return web.Response(text="Zack-Bot is running and operational!")

app_web = web.Application()
app_web.add_routes([web.get('/', handle)])

async def start_web_server():
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()
    logging.info("Web server started.")

# تهيئة عميل التيليجرام
client = TelegramClient('zack_bot', API_ID, API_HASH)

# معالجة ملفات الجلسات (Zip أو Session)
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    if not event.file: return
    path = await event.download_media()
    user_id = event.sender_id
    await event.respond("📂 جاري تحليل الملف...")
    
    added_count = 0
    if path.endswith('.zip'):
        extract_dir = f"sessions_{user_id}"
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.session'):
                        try:
                            # محاولة استخراج رقم الهاتف من ملف الجلسة
                            sess_client = TelegramClient(os.path.join(root, file).replace('.session', ''), API_ID, API_HASH)
                            await sess_client.connect()
                            if await sess_client.is_user_authorized():
                                me = await sess_client.get_me()
                                if me and me.phone:
                                    add_user_number(user_id, "+" + str(me.phone))
                                    added_count += 1
                            await sess_client.disconnect()
                        except: pass
        await event.respond(f"✅ تم استخراج {added_count} حساب بنجاح.")
    
    if os.path.exists(path): os.remove(path)

# الأوامر والتعامل مع الأزرار
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("👑 **أهلاً بك يا زاك في لوحة تحكم البوت:**", buttons=get_main_keyboard())

@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    
    if data == "admin_panel":
        await event.edit("⚙️ **لوحة التحكم المتقدمة:**", buttons=get_admin_panel_keyboard())
    elif data == "my_numbers":
        nums = get_user_numbers(user_id)
        text = "\n".join([f"📱 `{n}`" for n in nums]) if nums else "⚠️ لا توجد أرقام مسجلة."
        await event.edit(f"📱 **قائمة أرقامك:**\n\n{text}", buttons=get_back_keyboard())
    elif data == "add_number":
        user_states[user_id] = {"action": "waiting_for_phone"}
        await event.edit("➕ **أرسل الرقم الذي تريد إضافته (بالصيغة الدولية):**", buttons=get_back_keyboard())
    elif data == "back_home":
        await event.edit("👑 **القائمة الرئيسية:**", buttons=get_main_keyboard())
    elif data == "stats":
        await event.edit(f"📊 **إحصائيات النظام:**\n\n👤 المستخدم: `{user_id}`\n✅ الحالة: Super Admin", buttons=get_back_keyboard())
    else:
        await event.answer("جاري التطوير...", alert=True)

# معالجة النصوص للإضافات اليدوية
@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if not event.is_private or event.raw_text.startswith('/'): return
    user_id = event.sender_id
    if user_id in user_states and user_states[user_id].get("action") == "waiting_for_phone":
        phone = event.raw_text.strip()
        add_user_number(user_id, phone)
        await event.respond(f"✅ تم حفظ الرقم `{phone}` بنجاح في قاعدة البيانات!")
        user_states.pop(user_id, None)

# الدالة الرئيسية للتشغيل
async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Zack-Bot is UP and running!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
