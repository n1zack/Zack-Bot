import os
import logging
import zipfile
import asyncio
import datetime
import sqlite3
import aiohttp
from aiohttp import web
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import ImportChatInviteRequest, StartBotRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.chatlists import JoinChatlistInviteRequest, CheckChatlistInviteRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
from database import (
    init_db, add_user_number, get_user_numbers, get_session_string, 
    delete_user_number, add_subscriber, get_subscribers, is_subscribed
)
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة قاعدة البيانات
init_db()

# ================= بياناتك الثابتة المعتمدة =================
BOT_TOKEN = '8545427199:AAFr8eFKX6LUrGQCz9oRH14ASvzPYXLPJbs'
API_ID = 31470691  
API_HASH = '5c3f24ee62d7a7e46601a53f571f62cc'
ADMIN_ID = 1251313339
# ==========================================================

user_states = {}

# سيرفر الويب لضمان بقاء البوت نشطاً على Render
async def handle(request):
    return web.Response(text="Zack-Bot is running and fully operational!")

app_web = web.Application()
app_web.add_routes([web.get('/', handle)])

async def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Web server started on port {port}.")

# دالة إرسال Ping تلقائي للبوت كل 5 دقائق لمنع الخمول على Render
async def keep_alive():
    await asyncio.sleep(15)
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RENDER_URL) as response:
                    logger.info(f"Keep-Alive ping sent to {RENDER_URL}, status: {response.status}")
        except Exception as e:
            logger.error(f"Keep-Alive ping failed: {e}")
        
        await asyncio.sleep(300)

# اسم الجلسة
client = TelegramClient('zack_bot_super_admin', API_ID, API_HASH)

# --- أمر /start ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        user_id = event.sender_id
        user_states.pop(user_id, None)
        is_admin = (user_id == ADMIN_ID)
        
        sender = await event.get_sender()
        user_name = getattr(sender, 'first_name', 'صديقي') if sender else 'صديقي'
        
        # التحقق من الاشتراك إذا لم يكن مشرفاً
        if not is_admin and not is_subscribed(user_id):
            await event.respond(
                f"⚠️ **أنت غير مشترك في البوت.**\n"
                f"معرفك (ID): `{user_id}`\n"
                "قم بالتواصل مع @n1zack لتفعيل اشتراكك.",
                buttons=get_back_keyboard()
            )
            return

        if is_admin:
            welcome_text = (
                f"👑 **مرحباً بك مجدداً يا زاك (المشرف العام)**\n"
                f"معرفك (ID): `{user_id}`\n\n"
                "اختر العملية المطلوبة لإدارة الحسابات والجلسات والأرقام:"
            )
        else:
            welcome_text = (
                f"👋 **مرحباً بك {user_name} في البوت الشامل**\n"
                f"معرفك (ID): `{user_id}`\n\n"
                "اختر العملية المطلوبة:"
            )
            
        await event.respond(welcome_text, buttons=get_main_keyboard(is_admin))
    except Exception as e:
        logger.error(f"Error in start command: {e}")

# --- معالجة الأزرار الشفافة ---
@client.on(events.CallbackQuery)
async def callback_handler(event):
    try:
        data = event.data.decode('utf-8')
        user_id = event.sender_id
        
        if data not in ["back_home", "admin_panel"] and user_id != ADMIN_ID and not is_subscribed(user_id):
            await event.answer("⚠️ اشتراكك منتهٍ أو غير مفعل!", alert=True)
            await event.edit(
                f"⚠️ **أنت غير مشترك في البوت.**\n"
                f"معرفك (ID): `{user_id}`\n"
                "قم بالتواصل مع @n1zack لتفعيل اشتراكك.",
                buttons=get_back_keyboard()
            )
            return

        if data == "admin_panel":
            if user_id != ADMIN_ID:
                await event.answer("هذا القسم مخصص للمشرف فقط!", alert=True)
                return
            await event.answer()
            await event.edit("⚙️ **لوحة التحكم والإدارة:**\nاختر القسم المطلوب:", buttons=get_admin_panel_keyboard())

        elif data == "sub_user":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_sub"}
            await event.answer()
            await event.edit(
                "✅ **تفعيل اشتراك مستخدم:**\n"
                "أرسل البيانات بالصيغة التالية:\n`ID [رقم_الايدي] [عدد_الأيام] d`\n\n"
                "مثال: `ID 123456789 5 d`", buttons=get_back_keyboard()
            )

        elif data == "list_subs":
            if user_id != ADMIN_ID: return
            subs = get_subscribers()
            if subs:
                text = "👥 **قائمة المشتركين الحاليين:**\n\n"
                for sub in subs:
                    text += f"👤 ID: `{sub[0]}` | ⏳ ينتهي في: `{sub[1]}`\n"
            else:
                text = "👥 **قائمة المشتركين:**\nلا توجد اشتراكات مسجلة حالياً."
            await event.answer()
            await event.edit(text, buttons=get_back_keyboard())

        elif data == "stats":
            await event.answer()
            await event.edit(f"📊 **إحصائيات النظام:**\n- معرفك: `{user_id}`\n- الحالة: نشط ✅", buttons=get_back_keyboard())

        elif data == "msg_user":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_msg_user"}
            await event.answer()
            await event.edit(
                "✉️ **إرسال رسالة لمستخدم:**\n"
                "أرسل الرسالة بالصيغة التالية:\n`[ID] [النص]`\n\n"
                "مثال: `123456789 مرحباً بك`", buttons=get_back_keyboard()
            )

        elif data == "msg_all":
            if user_id != ADMIN_ID: return
            user_states[user_id] = {"action": "waiting_for_msg_all"}
            await event.answer()
            await event.edit(
                "📢 **إرسال رسالة للجميع:**\n"
                "أرسل النص الذي تريد إذاعته لكافة المستخدمين الآن:", buttons=get_back_keyboard()
            )

        elif data == "my_numbers":
            await event.answer()
            numbers = get_user_numbers(user_id)
            if numbers:
                numbers_list = "\n".join([f"📱 `{num}`" for num in numbers])
                text = f"📱 **أرقامك المسجلة خصيصاً لك (معزولة وآمنة):**\n\n{numbers_list}"
            else:
                text = "📱 **أرقامك المسجلة:**\nلا توجد أرقام مسجلة حالياً."
            await event.edit(text, buttons=get_back_keyboard())
        
        elif data == "add_number":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_phone"}
            await event.edit("➕ **إضافة رقم جديد:**\nالرجاء إرسال رقم الهاتف بالصيغة الدولية (مثال: `+96170123456`)", buttons=get_back_keyboard())
            
        elif data == "delete_number":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_delete"}
            await event.edit("➖ **حذف رقم:**\nأرسل الرقم الذي تريد حذفه من قائمتك.", buttons=get_back_keyboard())

        elif data == "session_login":
            await event.answer()
            await event.edit("📥 **تسجيل دخول عبر ملف جلسات:**\nأرسل ملف `zip` أو `sessions` أو `txt` وسأقوم بحفظ جلساته في قاعدة البيانات حصرياً لك.", buttons=get_back_keyboard())
            
        elif data == "export_sessions":
            await event.answer()
            nums = get_user_numbers(user_id)
            if not nums:
                return await event.edit("⚠️ لا توجد أرقام أو جلسات محفوظة لتصديرها.", buttons=get_back_keyboard())
            
            await event.edit("⏳ جاري إنشاء ملف الجلسات الخاص بك...")
            zip_filename = f"my_sessions_{user_id}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for phone in nums:
                    s_str = get_session_string(user_id, phone)
                    if s_str:
                        clean_phone = phone.replace('+', '')
                        txt_filename = f"{clean_phone}.txt"
                        with open(txt_filename, "w", encoding="utf-8") as f:
                            f.write(s_str)
                        zipf.write(txt_filename)
                        os.remove(txt_filename)
            
            if os.path.exists(zip_filename):
                await event.respond(file=zip_filename)
                os.remove(zip_filename)
                await event.edit("✅ **تم تصدير ملفات الجلسات بنجاح!**", buttons=get_back_keyboard())
            else:
                await event.edit("❌ لم يتم العثور على بيانات جلسات مرتبطة بأرقامك.", buttons=get_back_keyboard())

        elif data == "ref_bot":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_ref"}
            await event.edit("🤖 **تشغيل بوت عبر إحالة / Mini App:**\nأرسل رابط الإحالة أو البوت الآن.", buttons=get_back_keyboard())

        elif data == "join_chat":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_join"}
            await event.edit("📢 **انضمام لقناة أو مجموعة:**\nأرسل الرابط الآن.", buttons=get_back_keyboard())
            
        elif data == "leave_chat":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_leave"}
            await event.edit("🚪 **مغادرة قناة أو مجموعة:**\nأرسل الرابط للمغادرة.", buttons=get_back_keyboard())
            
        elif data == "join_folder":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_folder"}
            await event.edit("📁 **انضمام لمجلد قنوات:**\nأرسل رابط المجلد الآن.", buttons=get_back_keyboard())

        elif data == "send_reaction":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_reaction"}
            await event.edit("❤️ **تفاعل رياكشن:**\nأرسل رابط المنشور متبوعاً بالإيموجي (مثال:\n`https://t.me/channel/123 👍`)", buttons=get_back_keyboard())

        # --- ميزات زاك الإضافية ---
        elif data == "view_post":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_view"}
            await event.edit("👀 **زيادة مشاهدات منشور:**\nأرسل رابط المنشور الآن (مثال: `https://t.me/channel/123`)", buttons=get_back_keyboard())

        elif data == "check_accounts":
            await event.answer()
            nums = get_user_numbers(user_id)
            if not nums: 
                return await event.edit("⚠️ لا توجد أرقام مسجلة لديك لفحصها.", buttons=get_back_keyboard())
            
            await event.edit("⏳ جاري فحص حالة الحسابات، يرجى الانتظار...")
            alive, dead = 0, 0
            results = []
            for phone in nums:
                s_str = get_session_string(user_id, phone)
                try:
                    async with TelegramClient(StringSession(s_str), API_ID, API_HASH) as acc:
                        await acc.get_me()
                        alive += 1
                        results.append(f"✅ `{phone}`: نشط")
                except:
                    dead += 1
                    results.append(f"❌ `{phone}`: محذوف / خارج الخدمة")
            await event.edit(f"📊 **حالة الحسابات:**\nالنشطة: {alive} | المتعطلة: {dead}\n\n" + "\n".join(results), buttons=get_back_keyboard())

        elif data == "send_group_msg":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_group_msg"}
            await event.edit("💬 **إرسال رسائل لمجموعة:**\nأرسل رابط المجموعة ثم الرسالة (مثال:\n`https://t.me/group_link مرحباً جميعاً`)", buttons=get_back_keyboard())

        elif data == "comment_post":
            await event.answer()
            user_states[user_id] = {"action": "waiting_for_comment"}
            await event.edit("✍️ **التعليق على منشور:**\nأرسل رابط المنشور ثم نص التعليق (مثال:\n`https://t.me/channel/123 منشور رائع`)", buttons=get_back_keyboard())

        elif data == "back_home":
            await event.answer()
            user_states.pop(user_id, None)
            is_admin = (user_id == ADMIN_ID)
            
            if not is_admin and not is_subscribed(user_id):
                await event.edit(
                    f"⚠️ **أنت غير مشترك في البوت.**\n"
                    f"معرفك (ID): `{user_id}`\n"
                    "قم بالتواصل مع @n1zack لتفعيل اشتراكك.",
                    buttons=get_back_keyboard()
                )
                return

            sender = await event.get_sender()
            user_name = getattr(sender, 'first_name', 'صديقي') if sender else 'صديقي'
            
            if is_admin:
                welcome_text = f"👑 **مرحباً بك مجدداً يا زاك (المشرف العام)**\n\nاختر العملية المطلوبة:"
            else:
                welcome_text = f"👋 **مرحباً بك {user_name} من جديد**\n\nاختر العملية المطلوبة:"
                
            await event.edit(welcome_text, buttons=get_main_keyboard(is_admin))
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")

# --- معالجة الملفات المرسلة (تم تحديثها بالبحث العميق والشامل لتقبل كافة الملفات الخارجية والملفات النصية) ---
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    try:
        user_id = event.sender_id
        if user_id != ADMIN_ID and not is_subscribed(user_id):
            return await event.respond(
                f"⚠️ **أنت غير مشترك في البوت.**\n"
                f"معرفك (ID): `{user_id}`\n"
                "قم بالتواصل مع @n1zack لتفعيل اشتراكك."
            )

        path = await event.download_media()
        filename = event.file.name or ""
        await event.respond("📂 جاري فحص الملف واستخراج الجلسات بدقة سحابياً...")
        
        success_numbers = []
        extract_dir = f"temp_ext_{user_id}"
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as zip_err:
            logger.error(f"Not a valid zip or direct file: {zip_err}")
            # إذا لم يكن ملف مضغوط، ربما يكون ملفاً منفرداً تم إرساله مباشرة
            if filename.endswith('.session') or filename.endswith('.txt') or '.' not in filename:
                import shutil
                shutil.move(path, os.path.join(extract_dir, filename if filename else "temp_session.txt"))

        # البحث الشامل والعميق في كافة المجلدات والملفات الفرعية بدون استثناء
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                session_string = ""
                
                try:
                    # 1. فحص ملفات الـ session
                    if file.endswith('.session'):
                        temp_client = TelegramClient(file_path, API_ID, API_HASH)
                        await temp_client.connect()
                        if await temp_client.is_user_authorized():
                            session_string = temp_client.session.save()
                        await temp_client.disconnect()
                    
                    # 2. فحص الملفات النصية أو التكست الخارجية
                    elif file.endswith('.txt') or '.' not in file:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as rf:
                            content = rf.read().strip()
                            if len(content) > 30:
                                session_string = content

                    # التحقق والاعتماد النهائي للحساب
                    if session_string:
                        verify_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                        await verify_client.connect()
                        if await verify_client.is_user_authorized():
                            me = await verify_client.get_me()
                            if me and me.phone:
                                p_str = "+" + str(me.phone)
                                add_user_number(user_id, p_str, session_string)
                                if p_str not in success_numbers:
                                    success_numbers.append(p_str)
                        await verify_client.disconnect()
                            
                except Exception as ex:
                    logger.error(f"Error parsing file internal {file}: {ex}")
                    
        import shutil
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        if os.path.exists(path):
            os.remove(path)

        if success_numbers:
            await event.respond(f"✅ تمت إضافة الحسابات بنجاح وحفظها في قاعدتك الخاصة:\n" + "\n".join([f"- `{n}`" for n in success_numbers]))
        else:
            await event.respond("⚠️ لم يتم العثور على جلسات صالحة أو مطابقة للشروط داخل الملف المرفق.")

    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await event.respond(f"❌ حدث خطأ أثناء معالجة الملف: {e}")

# --- معالجة الرسائل النصية وحالات التفاعل ---
@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if not event.is_private or event.raw_text.startswith('/'):
        return
        
    user_id = event.sender_id
    text = event.raw_text.strip()
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        return
    
    if user_id not in user_states:
        return

    action = user_states[user_id].get("action")

    try:
        if action == "waiting_for_sub" and user_id == ADMIN_ID:
            parts = text.split()
            if parts[0].upper() == "ID" and parts[-1].lower() == "d":
                target_user_id = int(parts[1])
                days = int(parts[2])
                expiry = add_subscriber(target_user_id, days)
                await event.respond(f"✅ تم تفعيل الاشتراك للمستخدم `{target_user_id}` لمدة `{days}` أيام حتى `{expiry}`.")
                
                try:
                    await client.send_message(
                        target_user_id, 
                        f"🎉 **مبروك! تم تفعيل اشتراكك في البوت بنجاح.**\n⏳ تاريخ الانتهاء: `{expiry}`\n\nيمكنك الآن استخدام كافة ميزات البوت بكامل الصلاحيات."
                    )
                except Exception as ex:
                    logger.error(f"Could not notify user {target_user_id}: {ex}")
            user_states.pop(user_id, None)

        elif action == "waiting_for_msg_user" and user_id == ADMIN_ID:
            try:
                parts = text.split(maxsplit=1)
                target_user_id = int(parts[0])
                msg_text = parts[1]
                await client.send_message(target_user_id, f"📬 **رسالة من الإدارة:**\n\n{msg_text}")
                await event.respond(f"✅ تم إرسال الرسالة إلى المستخدم `{target_user_id}` بنجاح.")
            except Exception as ex:
                await event.respond(f"❌ فشل إرسال الرسالة (تأكد من الصيغة: ID النص): {ex}")
            user_states.pop(user_id, None)

        elif action == "waiting_for_msg_all" and user_id == ADMIN_ID:
            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM user_numbers UNION SELECT DISTINCT user_id FROM subscribers")
            all_users = [row[0] for row in cursor.fetchall()]
            conn.close()

            success_count = 0
            await event.respond(f"⏳ جاري إرسال الإذاعة إلى `{len(all_users)}` مستخدم...")
            
            for uid in all_users:
                if uid == ADMIN_ID: continue
                try:
                    await client.send_message(uid, f"📢 **إعلان عام من الإدارة:**\n\n{text}")
                    success_count += 1
                    await asyncio.sleep(0.2)
                except:
                    pass

            await event.respond(f"✅ تم إرسال الإذاعة بنجاح إلى `{success_count}` مستخدم.")
            user_states.pop(user_id, None)

        elif action == "waiting_for_phone":
            try:
                await event.respond("⏳ جاري الاتصال بخوادم تيليجرام وإرسال كود التحقق...")
                temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
                await temp_client.connect()
                
                sent = await temp_client.send_code_request(text)
                
                user_states[user_id]["phone"] = text
                user_states[user_id]["action"] = "waiting_for_code"
                user_states[user_id]["temp_client"] = temp_client
                user_states[user_id]["phone_code_hash"] = sent.phone_code_hash
                
                await event.respond(
                    "✅ **تم إرسال كود التحقق بنجاح!**\n\n"
                    "⚠️ ملاحظة هامة: الكود وصل إلى **تطبيق تيليجرام الرسمي** المفتوح على هذا الرقم (وليس رسالة SMS).\n"
                    "يرجى إرسال الكود الآن:"
                )
            except Exception as ex:
                logger.error(f"Error sending code to {text}: {ex}")
                await event.respond(f"❌ فشل إرسال الكود: `{ex}`\nتأكد من صحة الرقم بالصيغة الدولية (مثل `+961...`) ومن عدم وجود حظر مؤقت.")
                user_states.pop(user_id, None)

        elif action == "waiting_for_code":
            state = user_states[user_id]
            temp_client = state.get("temp_client")
            phone = state.get("phone")
            code = text
            
            if not temp_client or not phone:
                await event.respond("⚠️ حدث انقطاع في الجلسة المؤقتة. يرجى بدء إضافة الرقم من جديد عبر القائمة.")
                user_states.pop(user_id, None)
                return

            try:
                await temp_client.sign_in(phone=phone, code=code, phone_code_hash=state["phone_code_hash"])
                session_string = temp_client.session.save()
                add_user_number(user_id, phone, session_string)
                await temp_client.disconnect()
                
                await event.respond("🎉 **تم تسجيل الدخول بنجاح!**\nتم حفظ الرقم وجلسته في قاعدة البيانات حصرياً لك.")
                user_states.pop(user_id, None)
            except SessionPasswordNeededError:
                user_states[user_id]["action"] = "waiting_for_password"
                await event.respond("🔒 **الحساب محمي بالتحقق بخطوتين (كلمة المرور).**\nأرسل كلمة المرور الخاصة بالحساب الآن:")
            except Exception as ex:
                await event.respond(f"❌ الكود غير صحيح أو حدث خطأ: `{ex}`\nحاول إرسال الكود مجدداً أو ابدأ من جديد.")

        elif action == "waiting_for_password":
            state = user_states[user_id]
            temp_client = state.get("temp_client")
            phone = state.get("phone")
            password = text
            
            try:
                await temp_client.sign_in(password=password)
                session_string = temp_client.session.save()
                add_user_number(user_id, phone, session_string)
                await temp_client.disconnect()
                
                await event.respond("🎉 **تم تخطي التحقق بخطوتين بنجاح!**\nتم حفظ الحساب وأمانه في قاعدة البيانات.")
                user_states.pop(user_id, None)
            except Exception as ex:
                await event.respond(f"❌ كلمة المرور غير صحيحة: `{ex}`\nأعد إرسال كلمة المرور الصحيحة:")

        elif action == "waiting_for_delete":
            delete_user_number(user_id, text)
            await event.respond(f"🗑️ تم حذف الرقم `{text}` من قائمتك الخاصة.")
            user_states.pop(user_id, None)

        # --- معالجة الميزات الأخرى والتفاعلات ---
        elif action in [
            "waiting_for_ref", "waiting_for_join", "waiting_for_leave", 
            "waiting_for_folder", "waiting_for_reaction", "waiting_for_view", 
            "waiting_for_group_msg", "waiting_for_comment"
        ]:
            parts = text.split(maxsplit=1)
            link = parts[0]
            extra_text = parts[1] if len(parts) > 1 else ""
            emoji = extra_text if extra_text else "👍"
            
            nums = get_user_numbers(user_id)
            if not nums:
                await event.respond("⚠️ لا توجد أرقام مسجلة لديك لتنفيذ العملية.")
                user_states.pop(user_id, None)
                return

            await event.respond(f"⏳ جاري التنفيذ على `{len(nums)}` من حساباتك الخاصة...")
            success, fail = 0, 0

            for phone in nums:
                try:
                    s_str = get_session_string(user_id, phone)
                    if not s_str:
                        fail += 1
                        continue
                    
                    async with TelegramClient(StringSession(s_str), API_ID, API_HASH) as acc:
                        if action == "waiting_for_join":
                            if "+" in link or "joinchat" in link:
                                await acc(ImportChatInviteRequest(link.split("/")[-1].replace("+", "")))
                            else:
                                await acc(JoinChannelRequest(link.split("/")[-1].replace("@", "")))
                        elif action == "waiting_for_leave":
                            await acc(LeaveChannelRequest(link.split("/")[-1].replace("@", "")))
                        elif action == "waiting_for_ref":
                            if "startapp=" in link:
                                param = link.split("startapp=")[1].split("&")[0]
                                bot_u = link.split("/")[3].split("?")[0]
                                await acc(StartBotRequest(bot=bot_u, peer=bot_u, start_param=param))
                            elif "start=" in link:
                                parts_link = link.split("/")
                                bot_u = parts_link[-1].split("?")[0].replace("@", "")
                                param = link.split("start=")[1].split("&")[0]
                                await acc(StartBotRequest(bot=bot_u, peer=bot_u, start_param=param))
                            else:
                                bot_u = link.split("/")[-1].replace("@", "")
                                await acc(StartBotRequest(bot=bot_u, peer=bot_u, start_param=""))
                        elif action == "waiting_for_folder":
                            if "addlist" in link:
                                slug = link.split("addlist/")[-1]
                                invite = await acc(CheckChatlistInviteRequest(slug=slug))
                                await acc(JoinChatlistInviteRequest(slug=slug, peers=invite.peers))
                        elif action == "waiting_for_reaction":
                            parts_link = link.split("/")
                            channel_username = parts_link[-2]
                            msg_id = int(parts_link[-1])
                            entity = await acc.get_entity(channel_username)
                            await acc(SendReactionRequest(peer=entity, msg_id=msg_id, reaction=[ReactionEmoji(emoticon=emoji)]))
                        
                        elif action == "waiting_for_view":
                            parts_link = link.split("/")
                            msg_id = int(parts_link[-1])
                            channel = parts_link[-2]
                            await acc.get_messages(channel, ids=msg_id)
                        elif action == "waiting_for_group_msg":
                            await acc.send_message(link, extra_text)
                        elif action == "waiting_for_comment":
                            parts_link = link.split("/")
                            msg_id = int(parts_link[-1])
                            channel = parts_link[-2]
                            await acc.send_message(channel, extra_text, comment_to=msg_id)

                        success += 1
                except Exception as ex:
                    logger.error(f"Error for {phone}: {ex}")
                    fail += 1

            await event.respond(f"📊 **النتيجة لحساباتك الخاصة:**\n✅ نجحت: `{success}`\n❌ فشلت: `{fail}`")
            user_states.pop(user_id, None)
    except Exception as err:
        logger.error(f"Error in message handler: {err}")
        await event.respond(f"❌ حدث خطأ أثناء التنفيذ: `{str(err)}`")
        user_states.pop(user_id, None)

async def main():
    await start_web_server()
    asyncio.create_task(keep_alive())
    
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Zack-Bot started successfully with fixed export/import sessions.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
