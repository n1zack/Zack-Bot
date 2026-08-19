import os
import logging
import zipfile
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from database import init_db, add_user_number, get_user_numbers
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

logging.basicConfig(level=logging.INFO)
init_db()

# ================= بياناتك =================
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'
ADMIN_ID = 1251313339
# ==========================================

user_states = {}

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

client = TelegramClient('zack_bot', API_ID, API_HASH)

@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    if not event.file: return
    path = await event.download_media()
    user_id = event.sender_id
    await event.respond("📂 جاري المعالجة...")
    added_count = 0
    
    if path.endswith('.zip'):
        extract_dir = f"sessions_{user_id}"
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            for file in os.listdir(extract_dir):
                if file.endswith('.session'):
                    try:
                        sess_client = TelegramClient(os.path.join(extract_dir, file).replace('.session', ''), API_ID, API_HASH)
                        await sess_client.connect()
                        if await sess_client.is_user_authorized():
                            me = await sess_client.get_me()
                            if me and me.phone:
                                add_user_number(user_id, "+" + str(me.phone))
                                added_count += 1
                        await sess_client.disconnect()
                    except: pass
        await event.respond(f"✅ تم إضافة {added_count} حساب بنجاح لقائمتك.")
    if os.path.exists(path): os.remove(path)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("👑 **مرحباً بك يا زاك في لوحة تحكم البوت:**", buttons=get_main_keyboard())

@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    
    if data == "admin_panel":
        await event.edit("⚙️ **لوحة التحكم:**", buttons=get_admin_panel_keyboard())
    elif data == "my_numbers":
        nums = get_user_numbers(user_id)
        text = "\n".join([f"📱 `{n}`" for n in nums]) if nums else "لا توجد أرقام."
        await event.edit(f"📱 **أرقامك المسجلة:**\n\n{text}", buttons=get_back_keyboard())
    elif data == "add_number":
        user_states[user_id] = {"action": "waiting_for_phone"}
        await event.edit("➕ **أرسل الرقم بالصيغة الدولية:**", buttons=get_back_keyboard())
    elif data == "back_home":
        await event.edit("👑 **القائمة الرئيسية:**", buttons=get_main_keyboard())
    elif data == "stats":
        await event.edit(f"📊 **إحصائيات:**\n- ID: `{user_id}`\n- الحالة: Super Admin ✅", buttons=get_back_keyboard())
    else:
        await event.answer("قيد التطوير", alert=True)

@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if not event.is_private or event.raw_text.startswith('/'): return
    user_id = event.sender_id
    if user_id in user_states and user_states[user_id].get("action") == "waiting_for_phone":
        add_user_number(user_id, event.raw_text.strip())
        await event.respond("✅ تم حفظ الرقم يدوياً بنجاح!")
        user_states.pop(user_id, None)

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
 
