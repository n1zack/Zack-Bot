import os
import logging
import zipfile
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from database import init_db
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

logging.basicConfig(level=logging.INFO)
init_db()

# بياناتك الخاصة المعتمدة
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'
ADMIN_ID = 1251313339

# قاموس مؤقت لتخزين حالة المستخدمين (من ينتظر إدخال رقم أو كود)
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

# --- أمر /start الرئيسي ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    user_states.pop(user_id, null if 'null' in globals() else None) # مسح أي حالة سابقة
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
    
    if data == "admin_panel":
        await event.answer()
        await event.edit("⚙️ **لوحة التحكم والإدارة:**\nاختر القسم المطلوب:", buttons=get_admin_panel_keyboard())

    elif data == "my_numbers":
        await event.answer()
        await event.edit("📱 **أرقامك المسجلة:**\nلا توجد أرقام مسجلة حالياً باسمك.", buttons=get_back_keyboard())
    
    elif data == "add_number":
        await event.answer()
        # تعيين حالة المستخدم بأنه ينتظر إدخال رقم
        user_states[user_id] = {"action": "waiting_for_phone"}
        await event.edit(
            "➕ **إضافة رقم جديد:**\n"
            "الرجاء إرسال رقم الهاتف الآن بالصيغة الدولية (مثال: `+96170123456`)", 
            buttons=get_back_keyboard()
        )
        
    elif data == "session_login":
        await event.answer()
        await event.edit("📂 **أرسل ملف الجلسة الآن (Zip أو Session):**", buttons=get_back_keyboard())

    elif data == "back_home":
        await event.answer()
        user_states.pop(user_id, None)
        await event.edit("👑 **مرحباً بك من جديد يا زاك**", buttons=get_main_keyboard())
        
    else:
        await event.answer("عذراً، هذا الزر قيد البرمجة حالياً", alert=True)

# --- معالجة الرسائل النصية والملفات المرسلة من المستخدم ---
@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if event.is_private:
        user_id = event.sender_id
        text = event.raw_text.strip()
        
        # إذا كان المستخدم في حالة انتظار إدخال رقم هاتف
        if user_id in user_states and user_states[user_id].get("action") == "waiting_for_phone":
            phone_number = text
            user_states[user_id]["phone"] = phone_number
            
            await event.respond(f"⏳ جاري إرسال طلب رمز التحقق إلى الرقم `{phone_number}` عبر تليجرام...")
            
            try:
                # إنشاء عميل مؤقت لهذا الرقم لطلب الكود
                session_name = f"session_{user_id}_{phone_number.replace('+', '')}"
                temp_client = TelegramClient(session_name, API_ID, API_HASH)
                await temp_client.connect()
                
                # إرسال طلب كود التحقق
                sent = await temp_client.send_code_request(phone_number)
                user_states[user_id]["temp_client"] = temp_client
                user_states[user_id]["phone_code_hash"] = sent.phone_code_hash
                user_states[user_id]["action"] = "waiting_for_code"
                
                await event.respond(
                    "✅ **تم إرسال كود التحقق بنجاح!**\n"
                    "يرجى إرسال كود التحقق الذي وصلك إلى تطبيق تليجرام الآن (مثال: `12345`)."
                )
            except Exception as e:
                await event.respond(f"❌ حدث خطأ أثناء إرسال الكود: `{str(e)}`\nتأكد من صحة الرقم وأعد المحاولة.")
                user_states.pop(user_id, None)
                
        # إذا كان المستخدم في حالة انتظار كود التحقق (OTP)
        elif user_id in user_states and user_states[user_id].get("action") == "waiting_for_code":
            code = text
            state = user_states[user_id]
            temp_client = state["temp_client"]
            phone = state["phone"]
            phone_code_hash = state["phone_code_hash"]
            
            try:
                await temp_client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                await event.respond("🎉 **تم تسجيل الدخول بنجاح وحفظ الجلسة الخاصة بك وحدك! ✅**")
                user_states.pop(user_id, None)
            except SessionPasswordNeededError:
                user_states[user_id]["action"] = "waiting_for_password"
                await event.respond("🔒 **الحساب محمي بالتحقق بخطوتين (Password).**\nيرجى إرسال كلمة المرور الخاصة بحسابك الآن:")
            except Exception as e:
                await event.respond(f"❌ الكود غير صحيح أو حدث خطأ: `{str(e)}`")
                
        # إذا كان الحساب يتطلب كلمة مرور التحقق بخطوتين (2FA)
        elif user_id in user_states and user_states[user_id].get("action") == "waiting_for_password":
            password = text
            state = user_states[user_id]
            temp_client = state["temp_client"]
            
            try:
                await temp_client.sign_in(password=password)
                await event.respond("🎉 **تم تسجيل الدخول بنجاح وتفعيل الحساب بنجاح! 🔒**")
                user_states.pop(user_id, None)
            except Exception as e:
                await event.respond(f"❌ كلمة المرور غير صحيحة: `{str(e)}`")

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Telegram Bot started successfully with interactive phone login.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
 
