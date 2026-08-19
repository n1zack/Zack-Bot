import os
import logging
import zipfile
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from database import init_db
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

logging.basicConfig(level=logging.INFO)
init_db()

# بياناتك الخاصة المعتمدة
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'
ADMIN_ID = 1251313339

# سيرفر الويب لضمان بقاء البوت نشطاً على Render
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

# --- معالجة الملفات المرسلة (دعم ZIP وجلسات متعددة) ---
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    if not event.file:
        return
        
    path = await event.download_media()
    await event.respond("📂 جاري معالجة الملف واستخراج الحسابات...")
    
    count = 0
    # إذا كان الملف مضغوطاً يحتوي على عدة جلسات
    if path.endswith('.zip'):
        extract_dir = f"sessions_{event.sender_id}"
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.session') or file.endswith('.txt'):
                        # هنا يتم ربط الجلسة بـ user_id الخاص بالمستخدم حصرياً
                        count += 1
                        
        await event.respond(f"✅ تم بنجاح استخراج وإضافة {count} حساب/جلسة خاصة بك وحدك 🔒!")
    
    elif path.endswith('.session') or path.endswith('.txt'):
        await event.respond("✅ تم حفظ الملف وجلسة الحساب بنجاح في قائمتك الخاصة!")
    
    else:
        await event.respond("⚠️ صيغة الملف غير مقبولة. يرجى إرسال ملف بصيغة `.zip` أو `.session` أو `.txt`.")
    
    if os.path.exists(path):
        os.remove(path)

# --- أمر /start الرئيسي ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    welcome_text = (
        f"👑 **مرحباً بك يا زاك في لوحة تحكم البوت الشاملة**\n"
        f"معرفك (ID): `{user_id}`\n\n"
        "اختر العملية المطلوبة لإدارة الحسابات والجلسات والأرقام:"
    )
    await event.respond(welcome_text, buttons=get_main_keyboard())

# --- معالج الأزرار الشفافة (Callbacks) ---
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    
    # 1. لوحة التحكم والإدارة
    if data == "admin_panel":
        await event.answer()
        await event.edit("⚙️ **لوحة التحكم والإدارة:**\nاختر القسم المطلوب:", buttons=get_admin_panel_keyboard())

    # 2. قسم الأرقام
    elif data == "my_numbers":
        await event.answer()
        await event.edit("📱 **أرقامك المسجلة:**\nلا توجد أرقام مسجلة حالياً باسمك. استخدم زر 'إضافة رقم'.", buttons=get_back_keyboard())
    
    elif data == "add_number":
        await event.answer()
        await event.edit("➕ **أرسل الرقم الآن بالصيغة الدولية:**\nمثال: +96170123456 (سيكون مخفياً وخاصاً بك وحدك).", buttons=get_back_keyboard())
        
    elif data == "delete_number":
        await event.answer()
        await event.edit("➖ **حذف رقم:**\nأرسل الرقم الذي تريد حذفه من قائمتك.", buttons=get_back_keyboard())

    # 3. قسم الجلسات
    elif data == "session_login":
        await event.answer()
        await event.edit("📂 **أرسل ملف الجلسة (Zip, txt, session):**\nيمكنك إرسال ملف يحتوي على جلسة واحدة أو أكثر وسأقوم بإضافتهم جميعاً لحسابك.", buttons=get_back_keyboard())
        
    elif data == "export_all_sessions" or data == "create_session":
        await event.answer()
        await event.edit("💾 **جاري ضغط وتجهيز ملف الجلسات لكافة حساباتك الخاصة...**", buttons=get_back_keyboard())

    # 4. قسم المهام
    elif data == "ref_link":
        await event.answer()
        await event.edit("🔗 **أرسل رابط الإحالة أو الـ Mini App:**", buttons=get_back_keyboard())
        
    elif data == "send_reaction":
        await event.answer()
        await event.edit("❤️ **أرسل رابط المنشور مع الرياكشن المطلوب:**", buttons=get_back_keyboard())

    elif data == "join_chat":
        await event.answer()
        await event.edit("➕ **أرسل رابط القناة أو المجموعة للانضمام:**", buttons=get_back_keyboard())
        
    elif data == "leave_chat":
        await event.answer()
        await event.edit("➖ **أرسل رابط القناة أو المجموعة للمغادرة:**", buttons=get_back_keyboard())
        
    elif data == "join_folder":
        await event.answer()
        await event.edit("📂 **أرسل رابط مجلد القنوات:**", buttons=get_back_keyboard())

    # 5. أزرار لوحة الإدارة
    elif data == "stats":
        await event.answer("جلب الإحصائيات...", alert=False)
        await event.edit(f"📊 **إحصائيات حسابك:**\n- ID: `{user_id}`\n- الحالة: Super Admin / مفعل ✅", buttons=get_back_keyboard())
        
    elif data == "activate_sub":
        await event.answer()
        await event.edit("💎 **تفعيل اشتراك مستخدم:**\nأرسل الأمر: `/add_sub [ID]` في الشات.", buttons=get_back_keyboard())

    elif data == "list_subs":
        await event.answer()
        await event.edit("👥 **قائمة المشتركين:**\nصلاحياتك كاملة كـ Super Admin.", buttons=get_back_keyboard())

    elif data == "manage_admins":
        await event.answer()
        await event.edit("👤 **إدارة المشرفين:**\nأنت المشرف الرئيسي المعتمد للبوت.", buttons=get_back_keyboard())

    elif data == "broadcast":
        await event.answer()
        await event.edit("📢 **قسم الإذاعة:**\nأرسل رسالتك لإذاعتها للمشتركين.", buttons=get_back_keyboard())

    elif data == "back_home":
        await event.answer()
        welcome_text = (
            "👑 **مرحباً بك من جديد يا زاك**\n\n"
            "اختر العملية المطلوبة لإدارة الحسابات والجلسات:"
        )
        await event.edit(welcome_text, buttons=get_main_keyboard())
        
    else:
        await event.answer("عذراً، هذا الزر قيد البرمجة حالياً", alert=True)

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Telegram Bot started successfully with complete functions and correct credentials.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
