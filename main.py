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
from telethon.tl.functions.messages import ImportChatInviteRequest, StartBotRequest
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
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Neon database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Neon database: {e}")

init_db()

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

# --- واجهات وكيبوردات النظام ---
def get_main_keyboard(is_admin=False):
    keyboard = [
        [Button.inline("📱 أرقامي", "my_numbers"), Button.inline("➕ إضافة رقم", "add_number"), Button.inline("➖ حذف رقم", "delete_number")],
        [Button.inline("📥 تسجيل دخول (جلسات متعددة)", "session_login"), Button.inline("📤 تصدير الجلسات (ZIP)", "export_sessions")],
        [Button.inline("🤖 تشغيل بوت (إحالة / Mini App)", "ref_bot"), Button.inline("❤️ تفاعل رياكشن", "send_reaction")],
        [Button.inline("📢 انضمام لقناة/مجموعة", "join_chat"), Button.inline("🚪 مغادرة قناة/مجموعة", "leave_chat")],
        [Button.inline("📁 انضمام لمجلد", "join_folder")],
        [Button.inline("👀 زيادة مشاهدات", "view_post"), Button.inline("🔄 فحص الحسابات", "check_accounts")],
        [Button.inline("💬 رسالة للمجموعة", "send_group_msg"), Button.inline("✍️ تعليق على منشور", "comment_post")]
    ]
    if is_admin:
        keyboard.insert(0, [Button.inline("⚙️ لوحة التحكم", "admin_panel")])
    return keyboard

def get_admin_panel_keyboard():
    return [
        [Button.inline("✅ تفعيل اشتراك (ID)", "sub_user")],
        [Button.inline("👥 قائمة المشتركين", "list_subs"), Button.inline("📊 إحصائيات", "stats")],
        [Button.inline("✉️ رسالة لمستخدم", "msg_user"), Button.inline("📢 رسالة للكل", "msg_all")],
        [Button.inline("🔙 رجوع للقائمة الرئيسية", "back_home")]
    ]

def get_back_keyboard():
    return [
        [Button.inline("🔙 رجوع للقائمة الرئيسية", "back_home")]
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
        user_states.pop(user_id, None)
        is_admin = (user_id == ADMIN_ID)
        
        sender = await event.get_sender()
        user_name = getattr(sender, 'first_name', 'صديقي') if sender else 'صديقي'
        
        if not is_admin and not is_subscribed(user_id):
            await event.respond(
                f"⚠️ **أنت غير مشترك في البوت.**\nمعرفك (ID): `{user_id}`\nقم بالتواصل مع @n1zack لتفعيل اشتراكك.",
                buttons=get_back_keyboard()
            )
            return

        if is_admin:
            welcome_text = f"👑 **مرحباً بك مجدداً يا زاك (المشرف العام)**\nمعرفك الشخصي (ID): `{user_id}`\n\nاختر العملية المطلوبة من القائمة أدناه:"
        else:
            welcome_text = f"👋 **مرحباً بك {user_name}**\nمعرفك الشخصي (ID): `{user_id}`\n\nاختر العملية المطلوبة من القائمة أدناه:"
            
        await event.respond(welcome_text, buttons=get_main_keyboard(is_admin))
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@client.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        data = event.data.decode('utf-8')
        user_id = event.sender_id
        
        if data not in ["back_home", "admin_panel"] and user_id != ADMIN_ID and not is_subscribed(user_id):
            await event.answer("⚠️ عذراً، اشتراكك غير مفعل في النظام!", alert=True)
            return

        if data == "admin_panel":
            if user_id != ADMIN_ID: return
            await event.answer()
            await event.edit("⚙️ **لوحة تحكم المشرف العام:**\nاختر الإجراء المناسب:", buttons=get_admin_panel_keyboard())

        elif data == "sub_user":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_sub"}
            await event.answer()
            await event.edit("✅ **تفعيل اشتراك مستخدم:**\nأرسل بالصيغة التالية:\n`ID [أيدي_المستخدم] [عدد_الأيام] d`\nمثال: `ID 123456789 30 d`", buttons=get_back_keyboard())

        elif data == "list_subs":
            if user_id != ADMIN_ID: return
            subs = get_subscribers()
            text = "👥 **قائمة المشتركين النشطين:**\n\n" + ("\n".join([f"👤 ID: `{s[0]}` | ⏳ ينتهي في: `{s[1]}`" for s in subs]) if subs else "لا توجد أي اشتراكات مسجلة حالياً.")
            await event.answer()
            await event.edit(text, buttons=get_back_keyboard())

        elif data == "stats":
            await event.answer()
            await event.edit(f"📊 **إحصائيات النظام:**\n- معرف المستخدم: `{user_id}`\n- حالة الاتصال: مستقر ويعمل بكفاءة سحابياً عبر Neon ✅", buttons=get_back_keyboard())

        elif data == "msg_user":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_msg_user"}
            await event.answer()
            await event.edit("✉️ **مراسلة مستخدم محدد:**\nأرسل بالصيغة:\n`[ID_المستخدم] [نص_الرسالة]`", buttons=get_back_keyboard())

        elif data == "msg_all":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_msg_all"}
            await event.answer()
            await event.edit("📢 **إذاعة عامة:**\nأرسل نص الإذاعة الذي تريد إرساله لكافة المستخدمين الآن:", buttons=get_back_keyboard())

        elif data == "my_numbers":
            await event.answer()
            numbers = get_user_numbers(user_id)
            text = f"📱 **أرقامك المسجلة في القاعدة السحابية:**\n\n" + ("\n".join([f"📱 `{n}`" for n in numbers]) if numbers else "لا توجد أرقام مسجلة لديك حالياً.")
            await event.edit(text, buttons=get_back_keyboard())
        
        elif data == "add_number":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_phone"}
            await event.edit("➕ **إضافة رقم جديد:**\nأرسل رقم الهاتف بالصيغة الدولية الكاملة (مثال: `+961...`)", buttons=get_back_keyboard())
            
        elif data == "delete_number":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_delete"}
            await event.edit("➖ **حذف رقم:**\nأرسل الرقم المراد حذفه نهائياً من قائمتك:", buttons=get_back_keyboard())

        elif data == "session_login":
            await event.answer()
            await event.edit("📥 **رفع ملف الجلسات:**\nأرسل ملف الأرشيف بصيغة `zip` أو ملف نصي يحتوي على الجلسات أو ملفات `.session` وسأقوم بسحب الأرقام وحفظها سحابياً فوراً:", buttons=get_back_keyboard())
            
        elif data == "export_sessions":
            await event.answer()
            nums = get_user_numbers(user_id)
            if not nums: return await event.edit("⚠️ لا توجد أرقام مسجلة لتصدير جلساتها.", buttons=get_back_keyboard())
            
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
            await event.edit("✅ تم تصدير كافة جلساتك وإرسالها كملف مضغوط بنجاح!", buttons=get_back_keyboard())

        elif data == "ref_bot":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_ref"}
            await event.edit("🤖 **تشغيل بوت إحالة:**\nأرسل رابط الإحالة أو رابط البوت المطلوب:", buttons=get_back_keyboard())

        elif data == "join_chat":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_join"}
            await event.edit("📢 **انضمام لقناة أو مجموعة:**\nأرسل رابط القناة أو المجموعة للانضمام إليها بكافة حساباتك:", buttons=get_back_keyboard())
            
        elif data == "leave_chat":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_leave"}
            await event.edit("🚪 **مغادرة قناة أو مجموعة:**\nأرسل رابط القناة للمغادرة:", buttons=get_back_keyboard())
            
        elif data == "join_folder":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_folder"}
            await event.edit("📁 **انضمام لمجلد:**\nأرسل رابط المجلد المطلوب:", buttons=get_back_keyboard())

        elif data == "send_reaction":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_reaction"}
            await event.edit("❤️ **تفاعل رياكشن:**\nأرسل رابط المنشور متبوعاً بالإيموجي (مثال: `https://t.me/... 👍`):", buttons=get_back_keyboard())

        elif data == "view_post":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_view"}
            await event.edit("👀 **زيادة مشاهدات:**\nأرسل رابط المنشور لزيادة عدد المشاهدات عبر حساباتك:", buttons=get_back_keyboard())

        elif data == "check_accounts":
            await event.answer()
            nums = get_user_numbers(user_id)
            if not nums: return await event.edit("⚠️ لا توجد أرقام مسجلة لفحصها.", buttons=get_back_keyboard())
            await event.edit("⏳ **جاري فحص حالة الحسابات، يرجى الانتظار قليلاً...**")
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
                    res.append(f"❌ `{phone}`: محذوف أو معطل")
            await event.edit(f"📊 **نتيجة فحص الحسابات:**\n- الحسابات النشطة: `{alive}`\n- الحسابات المعطلة: `{dead}`\n\n" + "\n".join(res), buttons=get_back_keyboard())

        elif data == "send_group_msg":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_group_msg"}
            await event.edit("💬 **إرسال رسالة لمجموعة:**\nأرسل رابط المجموعة ثم نص الرسالة المطلوب إرسالها:", buttons=get_back_keyboard())

        elif data == "comment_post":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_comment"}
            await event.edit("✍️ **تعليق على منشور:**\nأرسل رابط المنشور ثم نص التعليق المطلوب:", buttons=get_back_keyboard())

        elif data == "back_home":
            await event.answer()
            user_states.pop(user_id, None)
            is_admin = (user_id == ADMIN_ID)
            await event.edit("👑 **القائمة الرئيسية للنظام:**", buttons=get_main_keyboard(is_admin))
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")

# --- معالجة ملفات الأرشيف والجلسات (المحدثة خصيصاً لقراءة ملفات SQLite .session الخارجية بدقة متناهية) ---
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

        await event.respond("🔍 **جاري قراءة محتوى ملفات الجلسات واستخراج البيانات برمجياً بدقة فائقة...**")
        success_numbers = []

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.startswith('info_') or file.lower() == 'readme.txt' or file.startswith('.'):
                    continue
                    
                f_path = os.path.join(root, file)
                session_str = ""
                try:
                    # قراءة ملفات SQLite .session واستخراج StringSession منها يدوياً وبرمجياً
                    if file.endswith('.session'):
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
                        except Exception as sql_ex:
                            logger.error(f"SQLite read error for {file}: {sql_ex}")
                    
                    elif file.endswith('.txt') or '.' not in file:
                        with open(f_path, "r", encoding="utf-8", errors="ignore") as rf:
                            content = rf.read().strip()
                            if len(content) > 20:
                                session_str = content

                    # التحقق وحفظ الرقم في قاعدة Neon السحابية
                    if session_str:
                        async with TelegramClient(StringSession(session_str), API_ID, API_HASH) as vc:
                            if await vc.is_user_authorized():
                                me = await vc.get_me()
                                if me and me.phone:
                                    phone_str = "+" + str(me.phone) if not str(me.phone).startswith("+") else str(me.phone)
                                    add_user_number(user_id, phone_str, session_str)
                                    if phone_str not in success_numbers:
                                        success_numbers.append(phone_str)
                except Exception as ex:
                    logger.error(f"Error parsing file {file}: {ex}")

        import shutil
        if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
        if os.path.exists(path): os.remove(path)

        if success_numbers:
            await event.respond(f"✅ **تم بنجاح استخراج وحفظ ({len(success_numbers)}) رقماً في قاعدتك السحابية:**\n" + "\n".join([f"- `{n}`" for n in success_numbers[:15]]))
        else:
            await event.respond("⚠️ لم يتم العثور على أي جلسات صالحة تفويضياً داخل هذا الأرشيف. تأكد أن الملفات تحتوي على بيانات جلسات حقيقية ونشطة.")
    except Exception as e:
        logger.error(f"Error handling archive: {e}")
        await event.respond(f"❌ حدث خطأ تقني أثناء معالجة الملف: {e}")

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
            cursor.execute("SELECT DISTINCT user_id FROM user_numbers UNION SELECT DISTINCT user_id FROM subscribers")
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

        elif action == "waiting_for_delete":
            delete_user_number(user_id, text)
            await event.respond(f"🗑️ **تم بنجاح حذف الرقم (`{text}`) من قاعدتك السحابية.**")
            user_states.pop(user_id, None)

        elif action in ["waiting_for_ref", "waiting_for_join", "waiting_for_leave", "waiting_for_folder", "waiting_for_reaction", "waiting_for_view", "waiting_for_group_msg", "waiting_for_comment"]:
            parts = text.split(maxsplit=1)
            link = parts[0]
            extra = parts[1] if len(parts) > 1 else "👍"
            nums = get_user_numbers(user_id)
            if not nums: return await event.respond("⚠️ لا توجد أرقام مسجلة لديك لتنفيذ هذه العملية.")
            
            await event.respond(f"⏳ **جاري تنفيذ العملية على (`{len(nums)}`) من حساباتك المسجلة...**")
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
                            await acc.get_messages(await acc.get_entity(p_l[-2]), ids=int(p_l[-1]))
                        elif action == "waiting_for_folder":
                            slug = link.split("/")[-1].replace("addlist/", "")
                            await acc(JoinChatlistInviteRequest(slug=slug, peers=[]))
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
