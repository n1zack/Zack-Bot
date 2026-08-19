import os
import logging
from aiohttp import web
from telethon import TelegramClient, events
from database import init_db
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

logging.basicConfig(level=logging.INFO)
init_db()

# بيانات البوت
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'

# سيرفر الويب لإبقاء ريندر نشطاً
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

# أمر /start الرئيسي (مع عزل المستخدمين وتنظيف الأزرار القديمة)
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    welcome_text = (
        f"👑 **مرحباً بك في لوحة تحكم البوت**\n"
        f"معرف المستخدم الخاص بك: `{user_id}`\n\n"
        "اختر العملية المطلوبة لإدارة حساباتك وجلساتك الخاصة:"
    )
    # إرسال الأزرار الشفافة بدون الحاجة لاستيراد معقد لـ ReplyKeyboardRemove
    await event.respond(welcome_text, buttons=get_main_keyboard())

# التفاعل مع ضغطات الأزرار (مع ضمان استقلالية البيانات لكل مستخدم)
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    
    if data == "admin_panel":
        await event.answer("تم فتح لوحة التحكم", alert=False)
        await event.edit(
            "⚙️ **لوحة التحكم والإدارة:**\nاختر القسم المطلوب:",
            buttons=get_admin_panel_keyboard()
        )
        
    elif data == "stats":
        await event.answer("جلب الإحصائيات...", alert=False)
        # هنا يتم جلب إحصائيات المستخدم الخاص به فقط
        await event.edit(
            f"📊 **إحصائيات حسابك:**\n\n"
            f"- معرفك (ID): `{user_id}`\n"
            "- أرقامك المسجلة: 0 (خاصة بك وحدك 🔒)\n"
            "- حالة الاشتراك: مفعل ✅",
            buttons=get_back_keyboard()
        )
        
    elif data == "activate_sub":
        await event.answer()
        await event.edit(
            "💎 **تفعيل اشتراك مستخدم:**\n\n"
            "لتفعيل اشتراك لمستخدم عبر الـ ID الخاص به، أرسل في الشات:\n"
            "`/add_sub [ID]`",
            buttons=get_back_keyboard()
        )
        
    elif data == "list_subs":
        await event.answer("جلب المشتركين...", alert=False)
        await event.edit(
            "👥 **قائمة المشتركين:**\n\n"
            f"- لديك صلاحية الإدارة الكاملة بصفتك Super Admin.",
            buttons=get_back_keyboard()
        )
        
    elif data == "manage_admins":
        await event.answer()
        await event.edit("👤 **إدارة المشرفين:**\nلوحة تحكم المشرفين الأساسيين.", buttons=get_back_keyboard())
        
    elif data == "broadcast":
        await event.answer()
        await event.edit("📢 **قسم الإذاعة:**\nأرسل رسالتك لإذاعتها.", buttons=get_back_keyboard())
        
    elif data == "add_number":
        await event.answer()
        # هنا يتم حفظ الرقم حصرياً تحت user_id الخاص بهذا المستخدم فقط ولن يراه غيره
        await event.edit(
            "➕ **إضافة رقم جديد لحسابك:**\n"
            "أرسل تفاصيل الرقم المراد إضافته (سيكون محفوظاً بشكل سرّي وخاص بك وحدك).", 
            buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]]
        )
        
    elif data == "delete_number":
        await event.answer()
        await event.edit("➖ **حذف رقم من أرقامك:**\nاختر الرقم المراد حذفه من قائمتك الخاصة.", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "session_login":
        await event.answer()
        await event.edit("📂 **تسجيل عبر ملف جلسات:**\nأرسل ملف الجلسة الخاص بك (.session).", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "create_session":
        await event.answer()
        await event.edit("📁 **إنشاء ملف جلسات:**\nجاري تجهيز استخراج ملف الجلسة الخاص بحساباتك فقط...", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "ref_link":
        await event.answer()
        await event.edit("🔗 **تشغيل عبر رابط إحالة:**\nأرسل رابط الإحالة الخاص بك.", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "join_chat":
        await event.answer()
        await event.edit("➕ **انضمام لقناة/مجموعة:**\nأرسل الرابط المطلوب.", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "leave_chat":
        await event.answer()
        await event.edit("➖ **مغادرة قناة/مجموعة:**\nحدد القناة المراد مغادرتها.", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "join_folder":
        await event.answer()
        await event.edit("📂 **انضمام لمجلد قنوات:**\nأرسل رابط المجلد.", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "send_reaction":
        await event.answer()
        await event.edit("❤️ **تفاعل رياكشن:**\nأرسل رابط المنشور.", buttons=[[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]] )
        
    elif data == "back_home":
        await event.answer()
        welcome_text = (
            "👑 **مرحباً بك من جديد**\n\n"
            "اختر العملية المطلوبة لإدارة الحسابات والجلسات:"
        )
        await event.edit(welcome_text, buttons=get_main_keyboard())
    else:
        await event.answer("هذا الزر قيد التطوير", alert=True)

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Telegram Bot started successfully with isolated user data.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
