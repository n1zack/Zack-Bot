import os
import logging
import zipfile
import asyncio
import datetime
import psycopg2
import sqlite3
import aiohttp
from aiohttp import web
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession, MemorySession
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import ImportChatInviteRequest, StartBotRequest, GetMessagesViewsRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.chatlists import JoinChatlistInviteRequest, CheckChatlistInviteRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

# إعدادات التسجيل الشاملة
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= بياناتك الثابتة المعتمدة =================
BOT_TOKEN = '8545427199:AAFr8eFKX6LUrGQCz9oRH14ASvzPYXLPJbs'
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
ADMIN_ID = 1251313339

# رابط قاعدة البيانات السحابية الجديدة (Neon.tech)
SUPABASE_URL = "postgresql://neondb_owner:npg_3AlBEIVMT0on@ep-lively-bonus-axwosu8s.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require"

# ==========================================================

# --- نظام اللغات والترجمات (Languages & Translations) ---
TRANSLATIONS = {
    'ar': {
        'admin_welcome': "👑 **مرحباً بك مجدداً يا زاك (المشرف العام)**\nمعرفك الشخصي (ID): `{user_id}`\n\nاختر العملية المطلوبة من القائمة أدناه:",
        'user_welcome': "👋 **مرحباً بك {user_name}**\nمعرفك الشخصي (ID): `{user_id}`\n\nاختر العملية المطلوبة من القائمة أدناه:",
        'not_subscribed': "⚠️ **أنت غير مشترك في البوت.**\nمعرفك (ID): `{user_id}`\nقم بالتواصل مع @n1zack لتفعيل اشتراكك.",
        'unauthorized_action': "⚠️ عذراً، اشتراكك غير مفعل في النظام!",
        
        # الأزرار الرئيسية
        'btn_my_numbers': "📱 أرقامي",
        'btn_add_number': "➕ إضافة رقم",
        'btn_del_number': "➖ حذف رقم",
        'btn_session_login': "📥 تسجيل دخول (جلسات متعددة)",
        'btn_export_sessions': "📤 تصدير الجلسات (ZIP)",
        'btn_ref_bot': "🤖 تشغيل بوت (إحالة / Mini App)",
        'btn_reaction': "❤️ تفاعل رياكشن",
        'btn_join_chat': "📢 انضمام لقناة/مجموعة",
        'btn_leave_chat': "🚪 مغادرة قناة/مجموعة",
        'btn_join_folder': "📁 انضمام لمجلد",
        'btn_view_post': "👀 زيادة مشاهدات",
        'btn_check_accounts': "🔄 فحص وتنظيف الحسابات",
        'btn_group_msg': "💬 رسالة للمجموعة",
        'btn_comment_post': "✍️ تعليق على منشور",
        'btn_admin_panel': "⚙️ لوحة التحكم",
        'btn_lang_switch': "🌐 English",
        
        # أزرار الإرجاع والتحكم
        'btn_back': "🔙 رجوع للقائمة الرئيسية",
        'btn_next': "التالي ➡️",
        'btn_prev': "⬅️ السابق",
        
        # لوحة المشرف والرسائل
        'admin_title': "⚙️ **لوحة تحكم المشرف العام:**\nاختر الإجراء المناسب:",
        'btn_sub_user': "✅ تفعيل اشتراك (ID)",
        'btn_list_subs': "👥 قائمة المشتركين",
        'btn_stats': "📊 إحصائيات",
        'btn_msg_user': "✉️ رسالة لمستخدم",
        'btn_msg_all': "📢 رسالة للكل",
        
        # رسائل الردود
        'lang_changed': "✅ تم تغيير اللغة بنجاح إلى الإنجليزية!",
        'no_numbers': "⚠️ لا توجد أرقام مسجلة لديك حالياً.",
        'my_numbers_title': "📱 **أرقامك المسجلة في القاعدة السحابية:**\n\n",
        'add_phone_prompt': "➕ **إضافة رقم جديد:**\nأرسل رقم الهاتف بالصيغة الدولية الكاملة (مثال: `+961...`)",
        'main_menu_title': "👑 **القائمة الرئيسية للنظام:**",
    },
    'en': {
        'admin_welcome': "👑 **Welcome back Zack (Super Admin)**\nYour ID: `{user_id}`\n\nChoose the required operation from the menu below:",
        'user_welcome': "👋 **Welcome {user_name}**\nYour ID: `{user_id}`\n\nChoose the required operation from the menu below:",
        'not_subscribed': "⚠️ **You are not subscribed to the bot.**\nYour ID: `{user_id}`\nPlease contact @n1zack to activate your subscription.",
        'unauthorized_action': "⚠️ Sorry, your subscription is not active in the system!",
        
        # Main Buttons
        'btn_my_numbers': "📱 My Numbers",
        'btn_add_number': "➕ Add Number",
        'btn_del_number': "➖ Delete Number",
        'btn_session_login': "📥 Session Login",
        'btn_export_sessions': "📤 Export Sessions (ZIP)",
        'btn_ref_bot': "🤖 Run Ref/Mini App Bot",
        'btn_reaction': "❤️ Send Reaction",
        'btn_join_chat': "📢 Join Chat",
        'btn_leave_chat': "🚪 Leave Chat",
        'btn_join_folder': "📁 Join Folder",
        'btn_view_post': "👀 View Post",
        'btn_check_accounts': "🔄 Check & Clean Accounts",
        'btn_group_msg': "💬 Group Message",
        'btn_comment_post': "✍️ Comment on Post",
        'btn_admin_panel': "⚙️ Admin Panel",
        'btn_lang_switch': "🌐 العربية",
        
        # Back & Navigation
        'btn_back': "🔙 Back to Main Menu",
        'btn_next': "Next ➡️",
        'btn_prev': "⬅️ Previous",
        
        # Admin Panel & Messages
        'admin_title': "⚙️ **Super Admin Control Panel:**\nChoose an appropriate action:",
        'btn_sub_user': "✅ Activate Subscription (ID)",
        'btn_list_subs': "👥 Subscribers List",
        'btn_stats': "📊 Statistics",
        'btn_msg_user': "✉️ Message User",
        'btn_msg_all': "📢 Broadcast to All",
        
        # Response Messages
        'lang_changed': "✅ Language changed successfully to Arabic!",
        'no_numbers': "⚠️ You have no numbers registered currently.",
        'my_numbers_title': "📱 **Your registered numbers in cloud database:**\n\n",
        'add_phone_prompt': "➕ **Add new number:**\nSend the phone number in full international format (e.g., `+961...`)",
        'main_menu_title': "👑 **Main System Menu:**",
    }
}

user_languages = {}

def get_user_lang(user_id):
    return user_languages.get(user_id, 'ar')

def toggle_user_lang(user_id):
    current = get_user_lang(user_id)
    new_lang = 'en' if current == 'ar' else 'ar'
    user_languages[user_id] = new_lang
    return new_lang

def t(user_id, key):
    lang = get_user_lang(user_id)
    return TRANSLATIONS.get(lang, TRANSLATIONS['ar']).get(key, key)

# --- بناء وتهيئة قاعدة البيانات السحابية (Neon / PostgreSQL) ---
def get_db_connection():
    return psycopg2.connect(SUPABASE_URL, connect_timeout=10)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_numbers (
                user_id BIGINT,
                phone TEXT,
                session_string TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id BIGINT PRIMARY KEY,
                expiry_date TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_users (
                user_id BIGINT PRIMARY KEY,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Neon database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Neon database: {e}")

init_db()

def register_bot_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO bot_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass

def get_total_bot_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bot_users")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except:
        return 0

def add_user_number(user_id, phone, session_string):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM user_numbers WHERE user_id = %s AND phone = %s", (user_id, phone))
    if cursor.fetchone():
        cursor.execute("UPDATE user_numbers SET session_string = %s WHERE user_id = %s AND phone = %s", (session_string, user_id, phone))
    else:
        cursor.execute("INSERT INTO user_numbers (user_id, phone, session_string) VALUES (%s, %s, %s)", (user_id, phone, session_string))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_numbers(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM user_numbers WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def get_session_string(user_id, phone):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM user_numbers WHERE user_id = %s AND phone = %s", (user_id, phone))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None

def delete_user_number(user_id, phone):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_numbers WHERE user_id = %s AND phone = %s", (user_id, phone))
    conn.commit()
    cursor.close()
    conn.close()

def is_subscribed(user_id):
    if user_id == ADMIN_ID:
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date FROM subscribers WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        expiry = datetime.datetime.strptime(row[0], "%Y-%m-%d")
        if expiry > datetime.datetime.now():
            return True
    return False

def add_subscriber(user_id, days):
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    expiry_str = expiry.strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subscribers (user_id, expiry_date) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET expiry_date = EXCLUDED.expiry_date",
        (user_id, expiry_str)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return expiry_str

def get_subscribers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expiry_date FROM subscribers")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# --- واجهات وكيبوردات النظام الديناميكية حسب لغة المستخدم ---
def get_main_keyboard(user_id, is_admin=False):
    keyboard = [
        [Button.inline(t(user_id, 'btn_my_numbers'), "my_numbers"), Button.inline(t(user_id, 'btn_add_number'), "add_number"), Button.inline(t(user_id, 'btn_del_number'), "del_page_0")],
        [Button.inline(t(user_id, 'btn_session_login'), "session_login"), Button.inline(t(user_id, 'btn_export_sessions'), "export_sessions")],
        [Button.inline(t(user_id, 'btn_ref_bot'), "ref_bot"), Button.inline(t(user_id, 'btn_reaction'), "send_reaction")],
        [Button.inline(t(user_id, 'btn_join_chat'), "join_chat"), Button.inline(t(user_id, 'btn_leave_chat'), "leave_chat")],
        [Button.inline(t(user_id, 'btn_join_folder'), "join_folder")],
        [Button.inline(t(user_id, 'btn_view_post'), "view_post"), Button.inline(t(user_id, 'btn_check_accounts'), "check_accounts")],
        [Button.inline(t(user_id, 'btn_group_msg'), "send_group_msg"), Button.inline(t(user_id, 'btn_comment_post'), "comment_post")],
        [Button.inline(t(user_id, 'btn_lang_switch'), "switch_language")]
    ]
    if is_admin:
        keyboard.insert(0, [Button.inline(t(user_id, 'btn_admin_panel'), "admin_panel")])
    return keyboard

def get_admin_panel_keyboard(user_id):
    return [
        [Button.inline(t(user_id, 'btn_sub_user'), "sub_user")],
        [Button.inline(t(user_id, 'btn_list_subs'), "list_subs"), Button.inline(t(user_id, 'btn_stats'), "stats")],
        [Button.inline(t(user_id, 'btn_msg_user'), "msg_user"), Button.inline(t(user_id, 'btn_msg_all'), "msg_all")],
        [Button.inline(t(user_id, 'btn_back'), "back_home")]
    ]

def get_back_keyboard(user_id):
    return [
        [Button.inline(t(user_id, 'btn_back'), "back_home")]
    ]

user_states = {}

# سيرفر الويب الشامل لمنع السكون على Render
async def handle(request):
    return web.Response(text="Zack-Bot Control Center Full Version is running successfully!")

app_web = web.Application()
app_web.add_routes([web.get('/', handle)])

async def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Web server started successfully on port {port}.")

async def keep_alive():
    await asyncio.sleep(15)
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com")
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RENDER_URL) as response:
                    logger.info(f"Keep-Alive ping sent successfully, status: {response.status}")
        except Exception as e:
            logger.error(f"Keep-Alive ping failed: {e}")
        await asyncio.sleep(300)

client = TelegramClient('zack_bot_control_massive', API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        user_id = event.sender_id
        register_bot_user(user_id)
        user_states.pop(user_id, None)
        is_admin = (user_id == ADMIN_ID)
        
        sender = await event.get_sender()
        user_name = getattr(sender, 'first_name', 'صديقي') if sender else 'صديقي'
        
        if not is_admin and not is_subscribed(user_id):
            await event.respond(
                t(user_id, 'not_subscribed').format(user_id=user_id),
                buttons=get_back_keyboard(user_id)
            )
            return

        if is_admin:
            welcome_text = t(user_id, 'admin_welcome').format(user_id=user_id)
        else:
            welcome_text = t(user_id, 'user_welcome').format(user_name=user_name, user_id=user_id)
            
        await event.respond(welcome_text, buttons=get_main_keyboard(user_id, is_admin))
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@client.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        data = event.data.decode('utf-8')
        user_id = event.sender_id
        
        # زر تبديل اللغة مستثنى من قيود الاشتراك ليعمل بحرية دائماً
        if data == "switch_language":
            toggle_user_lang(user_id)
            await event.answer(t(user_id, 'lang_changed'), alert=True)
            is_admin = (user_id == ADMIN_ID)
            sender = await event.get_sender()
            user_name = getattr(sender, 'first_name', 'صديقي') if sender else 'صديقي'
            if is_admin:
                welcome_text = t(user_id, 'admin_welcome').format(user_id=user_id)
            else:
                welcome_text = t(user_id, 'user_welcome').format(user_name=user_name, user_id=user_id)
            await event.edit(welcome_text, buttons=get_main_keyboard(user_id, is_admin))
            return

        if not data.startswith("del_page_") and not data.startswith("del_num_") and data not in ["back_home", "admin_panel"] and user_id != ADMIN_ID and not is_subscribed(user_id):
            await event.answer(t(user_id, 'unauthorized_action'), alert=True)
            return

        if data == "admin_panel":
            if user_id != ADMIN_ID: return
            await event.answer()
            await event.edit(t(user_id, 'admin_title'), buttons=get_admin_panel_keyboard(user_id))

        elif data == "sub_user":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_sub"}
            await event.answer()
            await event.edit("✅ **تفعيل اشتراك مستخدم:**\nأرسل بالصيغة التالية:\n`ID [أيدي_المستخدم] [عدد_الأيام] d`\nمثال: `ID 123456789 30 d`", buttons=get_back_keyboard(user_id))

        elif data == "list_subs":
            if user_id != ADMIN_ID: return
            subs = get_subscribers()
            text = "👥 **قائمة المشتركين النشطين:**\n\n" + ("\n".join([f"👤 ID: `{s[0]}` | ⏳ ينتهي في: `{s[1]}`" for s in subs]) if subs else "لا توجد أي اشتراكات مسجلة حالياً.")
            await event.answer()
            await event.edit(text, buttons=get_back_keyboard(user_id))

        elif data == "stats":
            if user_id != ADMIN_ID: return
            total_users = get_total_bot_users()
            subs = get_subscribers()
            await event.answer()
            await event.edit(f"📊 **إحصائيات النظام الشاملة:**\n- إجمالي الأشخاص الذين فتحوا البوت: `{total_users}` شخص\n- إجمالي المشتركين النشطين: `{len(subs)}` مشترك\n- حالة الاتصال: مستقر ويعمل بكفاءة سحابياً عبر Neon ✅", buttons=get_back_keyboard(user_id))

        elif data == "msg_user":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_msg_user"}
            await event.answer()
            await event.edit("✉️ **مراسلة مستخدم محدد:**\nأرسل بالصيغة:\n`[ID_المستخدم] [نص_الرسالة]`", buttons=get_back_keyboard(user_id))

        elif data == "msg_all":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_msg_all"}
            await event.answer()
            await event.edit("📢 **إذاعة عامة:**\nأرسل نص الإذاعة الذي تريد إرساله لكافة المستخدمين الآن:", buttons=get_back_keyboard(user_id))

        elif data == "my_numbers":
            await event.answer()
            numbers = get_user_numbers(user_id)
            text = t(user_id, 'my_numbers_title') + ("\n".join([f"📱 `{n}`" for n in numbers]) if numbers else t(user_id, 'no_numbers'))
            await event.edit(text, buttons=get_back_keyboard(user_id))
        
        elif data == "add_number":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_phone"}
            await event.edit(t(user_id, 'add_phone_prompt'), buttons=get_back_keyboard(user_id))
            
        elif data.startswith("del_page_"):
            await event.answer()
            page = int(data.split("_")[-1])
            numbers = get_user_numbers(user_id)
            
            if not numbers:
                await event.edit("⚠️ لا توجد أي أرقام مسجلة لحذفها.", buttons=get_back_keyboard(user_id))
                return
                
            per_page = 6  # 3 صفوف × 2 أزرار بجانب بعض
            total_pages = (len(numbers) + per_page - 1) // per_page
            page = max(0, min(page, total_pages - 1))
            
            current_nums = numbers[page * per_page : (page + 1) * per_page]
            
            keyboard = []
            row = []
            for num in current_nums:
                row.append(Button.inline(f"🗑️ حذف {num}", f"del_num_{page}_{num}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
                
            nav_buttons = []
            if page > 0:
                nav_buttons.append(Button.inline(t(user_id, 'btn_prev'), f"del_page_{page - 1}"))
            if page < total_pages - 1:
                nav_buttons.append(Button.inline(t(user_id, 'btn_next'), f"del_page_{page + 1}"))
            if nav_buttons:
                keyboard.append(nav_buttons)
                
            keyboard.append([Button.inline(t(user_id, 'btn_back'), "back_home")])
            
            await event.edit(f"➖ **قائمة أرقامك (الصفحة {page + 1} من {total_pages}):**\nانقر على زر الرقم أدناه لحذفه فوراً:", buttons=keyboard)

        elif data.startswith("del_num_"):
            parts = data.split("_")
            page = int(parts[2])
            phone_to_delete = parts[3]
            
            delete_user_number(user_id, phone_to_delete)
            await event.answer(f"✅ تم حذف الرقم {phone_to_delete} بنجاح!", alert=True)
            
            numbers = get_user_numbers(user_id)
            if not numbers:
                await event.edit("⚠️ لقد قمت بحذف كافة أرقامك. لم يتبق أي رقم مسجل.", buttons=get_back_keyboard(user_id))
                return
                
            per_page = 6
            total_pages = (len(numbers) + per_page - 1) // per_page
            page = min(page, total_pages - 1)
            current_nums = numbers[page * per_page : (page + 1) * per_page]
            
            keyboard = []
            row = []
            for num in current_nums:
                row.append(Button.inline(f"🗑️ حذف {num}", f"del_num_{page}_{num}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
                
            nav_buttons = []
            if page > 0:
                nav_buttons.append(Button.inline(t(user_id, 'btn_prev'), f"del_page_{page - 1}"))
            if page < total_pages - 1:
                nav_buttons.append(Button.inline(t(user_id, 'btn_next'), f"del_page_{page + 1}"))
            if nav_buttons:
                keyboard.append(nav_buttons)
                
            keyboard.append([Button.inline(t(user_id, 'btn_back'), "back_home")])
            
            await event.edit(f"➖ **قائمة أرقامك (الصفحة {page + 1} من {total_pages}):**\nانقر على زر الرقم أدناه لحذفه فوراً:", buttons=keyboard)

        elif data == "session_login":
            await event.answer()
            await event.edit("📥 **رفع ملف الجلسات:**\nأرسل ملف الأرشيف بصيغة `zip` أو ملف نصي يحتوي على الجلسات أو ملفات `.session` وسأقوم بسحب الأرقام وحفظها سحابياً فوراً:", buttons=get_back_keyboard(user_id))
            
        elif data == "export_sessions":
            await event.answer()
            nums = get_user_numbers(user_id)
            if not nums: return await event.edit("⚠️ لا توجد أرقام مسجلة لتصدير جلساتها.", buttons=get_back_keyboard(user_id))
            
            zip_filename = f"sessions_{user_id}.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for phone in nums:
                    s_str = get_session_string(user_id, phone)
                    if s_str:
                        t_name = f"{phone.replace('+', '')}.txt"
                        with open(t_name, "w", encoding="utf-8") as f: f.write(s_str)
                        zipf.write(t_name)
                        os.remove(t_name)
            await event.respond(file=zip_filename)
            os.remove(zip_filename)
            await event.edit("✅ تم تصدير كافة جلساتك وإرسالها كملف مضغوط بنجاح!", buttons=get_back_keyboard(user_id))

        elif data == "ref_bot":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_ref"}
            await event.edit("🤖 **تشغيل بوت إحالة:**\nأرسل رابط الإحالة أو رابط البوت المطلوب:", buttons=get_back_keyboard(user_id))

        elif data == "join_chat":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_join"}
            await event.edit("📢 **انضمام لقناة أو مجموعة:**\nأرسل رابط القناة أو المجموعة للانضمام إليها بكافة حساباتك:", buttons=get_back_keyboard(user_id))
            
        elif data == "leave_chat":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_leave"}
            await event.edit("🚪 **مغادرة قناة أو مجموعة:**\nأرسل رابط القناة للمغادرة:", buttons=get_back_keyboard(user_id))
            
        elif data == "join_folder":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_folder"}
            await event.edit("📁 **انضمام لمجلد:**\nأرسل رابط المجلد المطلوب:", buttons=get_back_keyboard(user_id))

        elif data == "send_reaction":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_reaction"}
            await event.edit("❤️ **تفاعل رياكشن:**\nأرسل رابط المنشور متبوعاً بالإيموجي (مثال: `https://t.me/... 👍`):", buttons=get_back_keyboard(user_id))

        elif data == "view_post":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_view"}
            await event.edit("👀 **زيادة مشاهدات:**\nأرسل رابط المنشور لزيادة عدد المشاهدات عبر حساباتك:", buttons=get_back_keyboard(user_id))

        elif data == "check_accounts":
            await event.answer()
            nums = get_user_numbers(user_id)
            if not nums: return await event.edit("⚠️ لا توجد أرقام مسجلة لفحصها.", buttons=get_back_keyboard(user_id))
            await event.edit("⏳ **جاري فحص وتصفية الحسابات تلقائياً، يرجى الانتظار...**")
            alive, dead = 0, 0
            res = []
            for phone in nums:
                s_str = get_session_string(user_id, phone)
                try:
                    async with TelegramClient(StringSession(s_str), API_ID, API_HASH) as acc:
                        await acc.get_me()
                        alive += 1
                        res.append(f"✅ `{phone}`: نشط ويعمل")
                except:
                    dead += 1
                    delete_user_number(user_id, phone)
                    res.append(f"🗑️ `{phone}`: معطل وتم حذفه تلقائياً")
            await event.edit(f"📊 **نتيجة فحص وتصفية الحسابات:**\n- الحسابات النشطة المتبقية: `{alive}`\n- الحسابات المعطلة (التي تم حذفها): `{dead}`\n\n" + "\n".join(res), buttons=get_back_keyboard(user_id))

        elif data == "send_group_msg":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_group_msg"}
            await event.edit("💬 **إرسال رسالة لمجموعة:**\nأرسل رابط المجموعة ثم نص الرسالة المطلوب إرسالها:", buttons=get_back_keyboard(user_id))

        elif data == "comment_post":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_comment"}
            await event.edit("✍️ **تعليق على منشور:**\nأرسل رابط المنشور ثم نص التعليق المطلوب:", buttons=get_back_keyboard(user_id))

        elif data == "back_home":
            await event.answer()
            user_states.pop(user_id, None)
            is_admin = (user_id == ADMIN_ID)
            await event.edit(t(user_id, 'main_menu_title'), buttons=get_main_keyboard(user_id, is_admin))
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")

# --- معالجة واستخراج الجلسات وتوليد StringSession السليم 100% من ملفات SQLite ---
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    try:
        user_id = event.sender_id
        if user_id != ADMIN_ID and not is_subscribed(user_id):
            return await event.respond("⚠️ عذراً، أنت غير مشترك في البوت لاستخدام هذه الميزة.")

        path = await event.download_media()
        extract_dir = f"extracted_full_{user_id}"
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception:
            import shutil
            shutil.move(path, os.path.join(extract_dir, "file_direct"))

        await event.respond("🔍 **جاري قراءة وتحويل الجلسات البرمجية واستخراج الـ StringSession الحقيقي بدقة...**")
        success_numbers = []
        detailed_errors = []

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                f_path = os.path.join(root, file)
                
                if file.endswith('.session') or '.' not in file or file.endswith('.txt'):
                    file_phone_candidate = "".join([c for c in file if c.isdigit()])
                    
                    if file.endswith('.txt') or '.' not in file:
                        try:
                            with open(f_path, 'r', encoding='utf-8', errors='ignore') as tf:
                                content = tf.read().strip()
                                if len(content) > 20:
                                    phone_str = None
                                    try:
                                        async with TelegramClient(StringSession(content), API_ID, API_HASH) as vc:
                                            if await vc.is_user_authorized():
                                                me = await vc.get_me()
                                                if me and me.phone:
                                                    phone_str = "+" + str(me.phone) if not str(me.phone).startswith("+") else str(me.phone)
                                    except:
                                        pass
                                    
                                    if not phone_str and len(file_phone_candidate) >= 10:
                                        phone_str = "+" + file_phone_candidate if not file_phone_candidate.startswith("+") else file_phone_candidate
                                    
                                    if phone_str:
                                        add_user_number(user_id, phone_str, content)
                                        if phone_str not in success_numbers:
                                            success_numbers.append(phone_str)
                                        continue
                        except:
                            pass

                    try:
                        phone_str = None
                        session_str = None
                        
                        try:
                            conn_sql = sqlite3.connect(f_path)
                            cursor_sql = conn_sql.cursor()
                            cursor_sql.execute("SELECT dc_id, server_address, port, auth_key FROM sessions LIMIT 1")
                            row = cursor_sql.fetchone()
                            conn_sql.close()
                            
                            if row:
                                dc_id, server_address, port, auth_key = row
                                mem_session = MemorySession()
                                mem_session.set_dc(dc_id, server_address, port)
                                mem_session.auth_key = auth_key
                                session_str = mem_session.save()
                        except Exception as sqlex:
                            detailed_errors.append(f"📁 المسار: `{f_path}`\n❌ خطأ قراءة SQLite: `{str(sqlex)}`")

                        if session_str:
                            try:
                                async with TelegramClient(StringSession(session_str), API_ID, API_HASH) as test_c:
                                    if await test_c.is_user_authorized():
                                        me = await test_c.get_me()
                                        if me and me.phone:
                                            phone_str = "+" + str(me.phone) if not str(me.phone).startswith("+") else str(me.phone)
                            except:
                                pass

                        if not phone_str and len(file_phone_candidate) >= 10:
                            phone_str = "+" + file_phone_candidate if not file_phone_candidate.startswith("+") else file_phone_candidate

                        if phone_str and session_str:
                            add_user_number(user_id, phone_str, session_str)
                            if phone_str not in success_numbers:
                                success_numbers.append(phone_str)
                        else:
                            if f_path not in str(detailed_errors):
                                detailed_errors.append(f"📁 المسار: `{f_path}`\n⚠️ تعذر توليد الـ StringSession بصورة صحيحة.")
                    except Exception as ex:
                        detailed_errors.append(f"📁 المسار: `{f_path}`\n❌ خطأ في معالجة الجلسة: `{str(ex)}`")

        import shutil
        if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
        if os.path.exists(path): os.remove(path)

        response_msg = ""
        if success_numbers:
            response_msg += f"✅ **تم تحديث واستخراج وحفظ ({len(success_numbers)}) رقماً وجلستها بنجاح تام:**\n" + "\n".join([f"- `{n}`" for n in success_numbers[:15]]) + "\n\n"
        else:
            response_msg += "❌ **لم يتم العثور على جلسات صالحة قابلة للتحويل.**\n\n"

        if detailed_errors:
            response_msg += "📋 **تقرير الملفات:**\n" + "\n\n".join(detailed_errors[:5])

        await event.respond(response_msg)
    except Exception as e:
        logger.error(f"Error handling archive: {e}")
        await event.respond(f"❌ حدث خطأ تقني عام أثناء معالجة الأرشيف: {e}")

# --- معالجة الحالات والمدخلات النصية ---
@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if not event.is_private or event.raw_text.startswith('/'): return
    user_id = event.sender_id
    text = event.raw_text.strip()
    if user_id not in user_states: return

    action = user_states[user_id].get("action")
    try:
        if action == "waiting_for_sub" and user_id == ADMIN_ID:
            parts = text.split()
            target_id, days = int(parts[1]), int(parts[2])
            expiry = add_subscriber(target_id, days)
            await event.respond(f"✅ **تم تفعيل الاشتراك بنجاح سحابياً:**\n- المستخدم: `{target_id}`\n- المدة: `{days}` أيام\n- تاريخ الانتهاء: `{expiry}`")
            try:
                await client.send_message(target_id, f"🎉 **مبروك! تم تفعيل اشتراكك في البوت بنجاح.**\n⏳ تاريخ الانتهاء: `{expiry}`\nيمكنك استخدام كافة ميزات البوت بكامل الصلاحيات.")
            except:
                pass
            user_states.pop(user_id, None)

        elif action == "waiting_for_msg_user" and user_id == ADMIN_ID:
            parts = text.split(maxsplit=1)
            target_id = int(parts[0])
            msg_content = parts[1]
            await client.send_message(target_id, f"📬 **رسالة رسمية من الإدارة:**\n\n{msg_content}")
            await event.respond(f"✅ تم إرسال الرسالة إلى المستخدم `{target_id}` بنجاح تام.")
            user_states.pop(user_id, None)

        elif action == "waiting_for_msg_all" and user_id == ADMIN_ID:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM user_numbers UNION SELECT DISTINCT user_id FROM subscribers UNION SELECT DISTINCT user_id FROM bot_users")
            all_users = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            success_cnt = 0
            await event.respond(f"⏳ **جاري إرسال الإذاعة العامة إلى (`{len(all_users)}`) مستخدم...**")
            for uid in all_users:
                if uid == ADMIN_ID: continue
                try:
                    await client.send_message(uid, f"📢 **إعلان هام من الإدارة:**\n\n{text}")
                    success_cnt += 1
                    await asyncio.sleep(0.2)
                except:
                    pass
            await event.respond(f"✅ **تمت الإذاعة بنجاح:** وصل الإعلان إلى (`{success_cnt}`) مستخدم.")
            user_states.pop(user_id, None)

        elif action == "waiting_for_phone":
            tc = TelegramClient(StringSession(), API_ID, API_HASH)
            await tc.connect()
            sent = await tc.send_code_request(text)
            user_states[user_id].update({"phone": text, "action": "waiting_for_code", "tc": tc, "hash": sent.phone_code_hash})
            await event.respond("✅ **تم إرسال كود التحقق بنجاح إلى تطبيق تيليجرام الخاص بالرقم.**\nأرسل كود التحقق الآن:")

        elif action == "waiting_for_code":
            st = user_states[user_id]
            try:
                await st["tc"].sign_in(phone=st["phone"], code=text, phone_code_hash=st["hash"])
                s_str = st["tc"].session.save()
                add_user_number(user_id, st["phone"], s_str)
                await st["tc"].disconnect()
                await event.respond("🎉 **تم تسجيل الدخول وحفظ الحساب في قاعدتك السحابية بنجاح تام!**")
                user_states.pop(user_id, None)
            except SessionPasswordNeededError:
                user_states[user_id]["action"] = "waiting_for_password"
                await event.respond("🔒 **هذا الحساب محمي بكلمة مرور (تحقق بخطوتين).**\nأرسل كلمة المرور الخاصة بالحساب الآن:")
            except Exception as ex:
                await event.respond(f"❌ كود التحقق خطأ أو انتهت صلاحيته: {ex}")

        elif action == "waiting_for_password":
            st = user_states[user_id]
            try:
                await st["tc"].sign_in(password=text)
                s_str = st["tc"].session.save()
                add_user_number(user_id, st["phone"], s_str)
                await st["tc"].disconnect()
                await event.respond("🎉 **تم تجاوز التحقق بخطوتين وحفظ الحساب سحابياً بنجاح تام!**")
                user_states.pop(user_id, None)
            except Exception as ex:
                await event.respond(f"❌ كلمة المرور غير صحيحة: {ex}")

        elif action in ["waiting_for_ref", "waiting_for_join", "waiting_for_leave", "waiting_for_folder", "waiting_for_reaction", "waiting_for_view", "waiting_for_group_msg", "waiting_for_comment"]:
            parts = text.split(maxsplit=1)
            link = parts[0]
            extra = parts[1] if len(parts) > 1 else "👍"
            nums = get_user_numbers(user_id)
            if not nums: return await event.respond("⚠️ لا توجد أرقام مسجلة لديك لتنفيذ هذه العملية.")
            
            await event.respond(f"⏳ **جاري تنفيذ العملية على حساباتك، يرجى الانتظار...**")
            succ, fail = 0, 0
            for phone in nums:
                s_str = get_session_string(user_id, phone)
                try:
                    async with TelegramClient(StringSession(s_str), API_ID, API_HASH) as acc:
                        if action == "waiting_for_join":
                            if "+" in link: await acc(ImportChatInviteRequest(link.split("/")[-1].replace("+", "")))
                            else: await acc(JoinChannelRequest(link.split("/")[-1].replace("@", "")))
                        elif action == "waiting_for_leave":
                            await acc(LeaveChannelRequest(link.split("/")[-1].replace("@", "")))
                        elif action == "waiting_for_ref":
                            bot_u = link.split("/")[-1].split("?")[0].replace("@", "")
                            param = link.split("start=")[1].split("&")[0] if "start=" in link else ""
                            await acc(StartBotRequest(bot=bot_u, peer=bot_u, start_param=param))
                        elif action == "waiting_for_reaction":
                            p_l = link.split("/")
                            await acc(SendReactionRequest(peer=await acc.get_entity(p_l[-2]), msg_id=int(p_l[-1]), reaction=[ReactionEmoji(emoticon=extra)]))
                        elif action == "waiting_for_view":
                            p_l = link.split("/")
                            channel_entity = await acc.get_entity(p_l[-2])
                            msg_id = int(p_l[-1])
                            await acc(GetMessagesViewsRequest(peer=channel_entity, id=[msg_id], increment=True))
                        elif action == "waiting_for_folder":
                            slug = link.split("/")[-1].replace("addlist/", "").split("?")[0]
                            folder_info = await acc(CheckChatlistInviteRequest(slug=slug))
                            await acc(JoinChatlistInviteRequest(slug=slug, peers=folder_info.peers))
                        elif action == "waiting_for_group_msg":
                            await acc.send_message(link, extra)
                        elif action == "waiting_for_comment":
                            p_l = link.split("/")
                            await acc.send_message(p_l[-2], extra, comment_to=int(p_l[-1]))
                        succ += 1
                except Exception as ex:
                    logger.error(f"Execution error on {phone}: {ex}")
                    fail += 1
                    
            await event.respond(f"📊 **النتيجة النهائية للتنفيذ:**\n- ✅ نجحت على: `{succ}` حساب\n- ❌ فشلت على: `{fail}` حساب")
            user_states.pop(user_id, None)
    except Exception as ex:
        logger.error(f"Error in user message handler: {ex}")
        await event.respond(f"❌ حدث خطأ غير متوقع أثناء معالجة طلبك: {ex}")
        user_states.pop(user_id, None)

async def main():
    await start_web_server()
    asyncio.create_task(keep_alive())
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Massive Control Bot started successfully with Neon and running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
