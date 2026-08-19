import os
import logging
import zipfile
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.tl.types import ReplyKeyboardRemove
from telethon.errors import SessionPasswordNeededError
from database import init_db, add_user_number, get_user_numbers
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

logging.basicConfig(level=logging.INFO)
init_db()

# ================= بياناتك الثابتة والمعتمدة =================
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'
ADMIN_ID = 1251313339
# ==========================================================

user_states = {}

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

# --- معالجة الملفات المرسلة (ZIP / Session / Txt) ---
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    if not event.file:
        return
        
    path = await event.download_media()
    await event.respond("📂 جاري معالجة الملف واستخراج الحسابات الخاصة بك...")
    
    count = 0
    if path.endswith('.zip'):
        extract_dir = f"sessions_{event.sender_id}"
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.session') or file.endswith('.txt'):
                        count += 1
                        
        await event.respond(f"✅ تم بنجاح استخراج وإضافة {count} جلسة خاصة بك وحدك 🔒!")
    
    elif path.endswith('.session') or path.endswith('.txt'):
        await event.respond("✅ تم حفظ الملف وجلسة الحساب بنجاح في قائمتك الخاصة!")
    
    else:
        await event.respond("⚠️ صيغة الملف غير مقبولة. يرجى إرسال ملف بصيغة `.zip` أو `.session`.")
    
    if os.path.exists(path):
        os.remove(path)

# --- أمر /start الرئيسي (مع مسح الأزرار الثابتة نهائياً) ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    user_states.pop(user_id, None)
    welcome_text = (
        f"👑 **مرحباً بك يا زاك في لوحة تحكم البوت الشاملة**\n"
        f"معرفك (ID): `{user_id}`\n\n"
        "اختر العملية المطلوبة لإدارة الحسابات والجلسات والأرقام:"
    )
    # استخدام ReplyKeyboardRemove() لحذف أي أزرار ثابتة قديمة من الشاشة
    await event.respond(welcome_text, buttons=[ReplyKeyboardRemove(), get_main_keyboard()])

# --- معالج الأزرار الشفافة (Callbacks) ---
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    
    if data == "admin_panel":
        await event.answer()
        await event.edit("⚙️ **لوحة التحكم والإدارة:**\nاختر القسم المطلوب:", buttons=get_admin_panel_keyboard())

    elif data == "my_numbers":
        await event.answer()
        numbers = get_user_numbers(user_id)
        if numbers:
            numbers_list = "\n".join([f"📱 `{num}`" for num in numbers])
            text = f"📱 **أرقامك المسجلة حالياً:**\n\n{numbers_list}"
        else:
            text = "📱 **أرقامك المسجلة:**\nلا توجد أرقام مسجلة حالياً باسمك. استخدم زر 'إضافة رقم'."
            
        await event.edit(text, buttons=get_back_keyboard())
    
    elif data == "add_number":
        await event.answer()
        user_states[user_id] = {"action": "waiting_for_phone"}
        await event.edit(
            "➕ **إضافة رقم جديد:**\n"
            "الرجاء إرسال رقم الهاتف الآن بالصيغة الدولية (مثال: `+96170123456`)", 
            buttons=get_back_keyboard()
        )
        
    elif data == "delete_number":
        await event.answer()
        await event.edit("➖ **حذف رقم:**\nأرسل الرقم الذي تريد حذفه من قائمتك.", buttons=get_back_keyboard())

    elif data == "session_login":
        await event.answer()
        await event.edit("📂 **أرسل ملف الجلسة (Zip أو Session):**\nسأقوم بمعالجته وإضافة الحسابات فوراً.", buttons=get_back_keyboard())
        
    elif data == "create_session" or data == "export_all_sessions":
        await event.answer()
        await event.edit("💾 **جاري ضغط وتجهيز ملف الجلسات لكافة حساباتك الخاصة...**", buttons=get_back_keyboard())

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

    elif data == "stats":
        await event.answer()
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
        user_states.pop(user_id, None)
        welcome_text = (
            "👑 **مرحباً بك من جديد يا زاك**\n\n"
            "اختر العملية المطلوبة لإدارة الحسابات والجلسات:"
        )
        await event.edit(welcome_text, buttons=get_main_keyboard())
        
    else:
        await event.answer("عذراً، هذا الزر قيد البرمجة حالياً", alert=True)

# --- معالجة إدخال النصوص وحفظ الرقم في قاعدة البيانات عند النجاح ---
@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if event.is_private and not event.raw_text.startswith('/'):
        user_id = event.sender_id
        text = event.raw_text.strip()
        
        # 1. مرحلة انتظار إدخال الرقم
        if user_id in user_states and user_states[user_id].get("action") == "waiting_for_phone":
            phone_number = text
            user_states[user_id]["phone"] = phone_number
            
            await event.respond(f"⏳ جاري إرسال طلب كود التحقق إلى الرقم `{phone_number}`...")
            
            try:
                session_name = f"session_{user_id}_{phone_number.replace('+', '')}"
                temp_client = TelegramClient(session_name, API_ID, API_HASH)
                await temp_client.connect()
                
                sent = await temp_client.send_code_request(phone_number)
                user_states[user_id]["temp_client"] = temp_client
                user_states[user_id]["phone_code_hash"] = sent.phone_code_hash
                user_states[user_id]["action"] = "waiting_for_code"
                
                await event.respond("✅ **تم إرسال كود التحقق بنجاح!**\nأرسل الكود الآن (مثال: `12345`).")
            except Exception as e:
                await event.respond(f"❌ حدث خطأ: `{str(e)}`\nتأكد من صحة الرقم وأعد المحاولة.")
                user_states.pop(user_id, None)
                
        # 2. مرحلة انتظار كود التحقق (OTP)
        elif user_id in user_states and user_states[user_id].get("action") == "waiting_for_code":
            code = text
            state = user_states[user_id]
            temp_client = state["temp_client"]
            phone = state["phone"]
            phone_code_hash = state["phone_code_hash"]
            
            try:
                await temp_client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                
                # حفظ الرقم في قاعدة البيانات فوراً عند النجاح
                add_user_number(user_id, phone)
                
                await event.respond("🎉 **تم تسجيل الدخول وحفظ الجلسة والرقم بنجاح وخاصة بك وحدك! ✅**")
                user_states.pop(user_id, None)
            except SessionPasswordNeededError:
                user_states[user_id]["action"] = "waiting_for_password"
                await event.respond("🔒 **الحساب محمي بكلمة مرور (التحقق بخطوتين).**\nيرجى إرسال كلمة المرور الآن:")
            except Exception as e:
                await event.respond(f"❌ الكود غير صحيح: `{str(e)}`")
                
        # 3. مرحلة التحقق بخطوتين (2FA)
        elif user_id in user_states and user_states[user_id].get("action") == "waiting_for_password":
            password = text
            state = user_states[user_id]
            temp_client = state["temp_client"]
            phone = state["phone"]
            
            try:
                await temp_client.sign_in(password=password)
                
                # حفظ الرقم في قاعدة البيانات عند تخطي التحقق بخطوتين
                add_user_number(user_id, phone)
                
                await event.respond("🎉 **تم تسجيل الدخول بنجاح تام وتفعيل الحساب وحفظه! 🔒**")
                user_states.pop(user_id, None)
            except Exception as e:
                await event.respond(f"❌ كلمة المرور غير صحيحة: `{str(e)}`")

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Zack-Bot started successfully with database and fixed keyboards.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
