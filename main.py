import os
import logging
from aiohttp import web
from telethon import TelegramClient, events
from database import init_db
from keyboards import get_main_keyboard, get_back_keyboard

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

# أمر /start الرئيسي
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    welcome_text = (
        "👑 **مرحباً بك يا زاك في لوحة تحكم Super Admin**\n\n"
        "إليك لوحة التحكم الشاملة لإدارة الحسابات والجلسات والأزرار:"
    )
    await event.respond(welcome_text, buttons=get_main_keyboard())

# التفاعل مع ضغطات الأزرار
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    
    if data == "admin_panel":
        await event.answer("تم فتح لوحة التحكم", alert=False)
        await event.edit(
            "⚙️ **لوحة التحكم الرئيسية:**\nاختر القسم المطلوبة لإدارة الأرقام:",
            buttons=[
                [Button.inline("➕ إضافة رقم", b"add_number"), Button.inline("➖ حذف رقم", b"delete_number")],
                [Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]
            ]
        )
        
    elif data == "stats":
        await event.answer("جلب الإحصائيات...", alert=False)
        await event.edit(
            "📊 **إحصائيات البوت:**\n\n"
            "- إجمالي المشتركين: 1\n"
            "- الحسابات المسجلة: 0\n"
            "- حالة السيرفر: متصل ✅",
            buttons=get_back_keyboard()
        )
        
    elif data == "add_number":
        await event.answer()
        await event.edit("➕ **إضافة رقم جديد:**\nأرسل تفاصيل الرقم المطلوب إضافته.", buttons=get_back_keyboard())
        
    elif data == "delete_number":
        await event.answer()
        await event.edit("➖ **حذف رقم مسجل:**\nحدد الرقم المراد حذفه من قاعدة البيانات.", buttons=get_back_keyboard())
        
    elif data == "session_login":
        await event.answer()
        await event.edit("📂 **تسجيل عبر ملف جلسات:**\nأرسل ملف الجلسة (.session) لتسجيل الدخول به.", buttons=get_back_keyboard())
        
    elif data == "create_session":
        await event.answer()
        await event.edit("📁 **إنشاء ملف جلسات:**\nجاري تجهيز استخراج ملفات الجلسات لجميع الحسابات...", buttons=get_back_keyboard())
        
    elif data == "ref_link":
        await event.answer()
        await event.edit("🔗 **تشغيل عبر رابط إحالة:**\nأرسل رابط الدعوة أو الإحالة لتنفيذ العملية.", buttons=get_back_keyboard())
        
    elif data == "join_chat":
        await event.answer()
        await event.edit("➕ **انضمام لقناة أو مجموعة:**\nأرسل معرف (Username) أو رابط القناة/المجموعة للانضمام.", buttons=get_back_keyboard())
        
    elif data == "leave_chat":
        await event.answer()
        await event.edit("➖ **مغادرة قناة أو مجموعة:**\nأرسل معرف القناة أو المجموعة المراد مغادرتها.", buttons=get_back_keyboard())
        
    elif data == "join_folder":
        await event.answer()
        await event.edit("📂 **انضمام لمجلد قنوات أو مجموعات:**\nأرسل رابط المجلد للانضمام بكافة محتوياته.", buttons=get_back_keyboard())
        
    elif data == "send_reaction":
        await event.answer()
        await event.edit("❤️ **تفاعل رياكشن:**\nأرسل رابط المنشور والرياكشن المطلوب وضعه.", buttons=get_back_keyboard())
        
    elif data == "activate_sub":
        await event.answer()
        await event.edit("💎 **تفعيل اشتراك مستخدم:**\nأرسل الأمر `/add_sub [ID]` لتفعيل الاشتراك.", buttons=get_back_keyboard())
        
    elif data == "list_subs":
        await event.answer("جلب قائمة المشتركين...", alert=False)
        await event.edit("👥 **قائمة المشتركين النشطين:**\n1. Zack (ID: 1251313339) - Super Admin 👑", buttons=get_back_keyboard())
        
    elif data == "manage_admins":
        await event.answer()
        await event.edit("👤 **إدارة المشرفين:**\nأنت المشرف الأساسي (Super Admin) لهذا البوت.", buttons=get_back_keyboard())
        
    elif data == "broadcast":
        await event.answer()
        await event.edit("📢 **قسم الإذاعة والتوجيه:**\nأرسل الرسالة التي تريد إذاعتها للمشتركين.", buttons=get_back_keyboard())
        
    elif data == "back_home":
        await event.answer()
        welcome_text = (
            "👑 **مرحباً بك من جديد يا زاك**\n\n"
            "إليك لوحة التحكم الشاملة لإدارة الحسابات والجلسات والأزرار:"
        )
        await event.edit(welcome_text, buttons=get_main_keyboard())
    else:
        await event.answer("هذا الزر قيد التطوير يا زاك", alert=True)

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logging.info("Telegram Bot started successfully with all features.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
 
