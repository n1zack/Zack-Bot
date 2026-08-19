import os
import logging
import zipfile
import asyncio
import datetime
from aiohttp import web
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import ImportChatInviteRequest, StartBotRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.chatlists import JoinChatlistInviteRequest, CheckChatlistInviteRequest
from database import init_db, add_user_number, get_user_numbers, delete_user_number, add_subscriber, get_subscribers, is_subscribed
from keyboards import get_main_keyboard, get_admin_panel_keyboard, get_back_keyboard

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# تهيئة قاعدة البيانات
init_db()

# ================= بياناتك الثابتة المعتمدة =================
BOT_TOKEN = '8545427199:AAG5hZC0DypVhE8xFuwOOEWrqwuirh_hutc'
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

# تهيئة عميل التيليجرام الأساسي للبوت
client = TelegramClient('zack_bot', API_ID, API_HASH)

# --- أمر /start ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    user_states.pop(user_id, None)
    is_admin = (user_id == ADMIN_ID)
    
    welcome_text = (
        f"👑 **مرحباً بك يا زاك في لوحة تحكم البوت الشاملة**\n"
        f"معرفك (ID): `{user_id}`\n\n"
        "اختر العملية المطلوبة لإدارة الحسابات والجلسات والأرقام:"
    )
    await event.respond(welcome_text, buttons=get_main_keyboard(is_admin))

# --- معالجة الأزرار الشفافة ---
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id
    
    # التحقق من الاشتراك للأقسام العادية (باستثناء المشرف أو العودة للرئيسية)
    if data not in ["back_home", "admin_panel"] and user_id != ADMIN_ID and not is_subscribed(user_id):
        await event.answer("⚠️ اشتراكك منتهٍ أو غير مفعل!", alert=True)
        await event.edit("⚠️ عذراً، أنت غير مشترك في البوت.\nقم بالتواصل مع @n1zack لتفعيل اشتراكك.", buttons=get_back_keyboard())
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

    elif data == "msg_user" or data == "msg_all":
        await event.answer("قيد التطوير في التحديث القادم", alert=True)

    elif data == "my_numbers":
        await event.answer()
        numbers = get_user_numbers(user_id)
        if numbers:
            numbers_list = "\n".join([f"📱 `{num}`" for num in numbers])
            text = f"📱 **أرقامك المسجلة خصيصاً لك:**\n\n{numbers_list}"
        else:
            text = "📱 **أرقامك المسجلة:**\nلا توجد أرقام مسجلة حالياً. استخدم زر 'إضافة رقم' أو أرسل ملف جلسات."
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
        user_states[user_id] = {"action": "waiting_for_delete"}
        await event.edit("➖ **حذف رقم:**\nأرسل الرقم الذي تريد حذفه من قائمتك الخاصة.", buttons=get_back_keyboard())

    elif data == "session_login":
        await event.answer()
        await event.edit("📥 **تسجيل دخول عبر ملف جلسات:**\nأرسل أي ملف بصيغة `zip` أو `sessions` أو `txt` وسأقوم بمعالجته واستخراج كافة الحسابات وإضافتها لقائمتك.", buttons=get_back_keyboard())
        
    elif data == "ref_bot":
        await event.answer()
        user_states[user_id] = {"action": "waiting_for_ref"}
        await event.edit("🤖 **تشغيل بوت عبر إحالة / Mini App:**\nأرسل رابط الإحالة أو رابط البوت الآن لتوجيه الحسابات.", buttons=get_back_keyboard())

    elif data == "join_chat":
        await event.answer()
        user_states[user_id] = {"action": "waiting_for_join"}
        await event.edit("📢 **انضمام لقناة أو مجموعة:**\nأرسل رابط القناة أو المجموعة (عام أو خاص).", buttons=get_back_keyboard())
        
    elif data == "leave_chat":
        await event.answer()
        user_states[user_id] = {"action": "waiting_for_leave"}
        await event.edit("🚪 **مغادرة قناة أو مجموعة:**\nأرسل رابط القناة أو المجموعة للمغادرة.", buttons=get_back_keyboard())
        
    elif data == "join_folder":
        await event.answer()
        user_states[user_id] = {"action": "waiting_for_folder"}
        await event.edit("📁 **انضمام لمجلد قنوات:**\nأرسل رابط المجلد وسأقوم بإجبار الحسابات على الانضمام للمجلد ولكافة محتوياته.", buttons=get_back_keyboard())

    elif data == "back_home":
        await event.answer()
        user_states.pop(user_id, None)
        is_admin = (user_id == ADMIN_ID)
        welcome_text = f"👑 **مرحباً بك من جديد يا زاك**\n\nاختر العملية المطلوبة:"
        await event.edit(welcome_text, buttons=get_main_keyboard(is_admin))
        
    else:
        await event.answer("عذراً، هذا الزر قيد التطوير", alert=True)

# --- معالجة الملفات المرسلة (ZIP, sessions, txt) ---
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    user_id = event.sender_id
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        await event.respond("⚠️ عذراً، أنت غير مشترك في البوت. قم بالتواصل مع @n1zack لتفعيل اشتراكك.")
        return

    path = await event.download_media()
    filename = event.file.name or ""
    await event.respond("📂 جاري فحص الملف ومعالجة الجلسات بدقة...")
    
    success_numbers = []
    failed_reasons = []

    try:
        if filename.endswith('.zip') or path.endswith('.zip'):
            extract_dir = f"sessions_{user_id}"
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith('.session') or file.endswith('.txt'):
                            file_path = os.path.join(root, file)
                            session_name_prefix = os.path.join(extract_dir, file.replace('.session', '').replace('.txt', ''))
                            try:
                                sess_client = TelegramClient(session_name_prefix, API_ID, API_HASH)
                                await sess_client.connect()
                                if await sess_client.is_user_authorized():
                                    me = await sess_client.get_me()
                                    if me and me.phone:
                                        phone_str = "+" + str(me.phone)
                                        add_user_number(user_id, phone_str)
                                        success_numbers.append(phone_str)
                                await sess_client.disconnect()
                            except Exception as e:
                                failed_reasons.append(f"{file}: {str(e)}")
        
        elif filename.endswith('.session') or filename.endswith('.txt') or path.endswith('.session') or path.endswith('.txt'):
            try:
                base_name = path.replace('.session', '').replace('.txt', '')
                sess_client = TelegramClient(base_name, API_ID, API_HASH)
                await sess_client.connect()
                if await sess_client.is_user_authorized():
                    me = await sess_client.get_me()
                    if me and me.phone:
                        phone_str = "+" + str(me.phone)
                        add_user_number(user_id, phone_str)
                        success_numbers.append(phone_str)
                await sess_client.disconnect()
            except Exception as e:
                failed_reasons.append(f"الملف الفردي: {str(e)}")

        report = "📊 **تقرير معالجة ملفات الجلسات:**\n\n"
        if success_numbers:
            report += f"✅ **تمت الإضافة بنجاح للأرقام التالية:**\n" + "\n".join([f"- `{n}`" for n in success_numbers]) + "\n\n"
        else:
            report += "⚠️ لم يتم العثور على أرقام نشطة صالحة للإضافة أو فشلت الجلسة.\n\n"
            
        if failed_reasons:
            report += f"❌ **أسباب الفشل لبعض الملفات:**\n" + "\n".join([f"- `{r}`" for r in failed_reasons])

        await event.respond(report)
    except Exception as ex:
        await event.respond(f"❌ حدث خطأ أثناء قراءة الملف: `{str(ex)}`")

    if os.path.exists(path):
        os.remove(path)

# --- معالجة المدخلات النصية وحالات التفاعل ---
@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if not event.is_private or event.raw_text.startswith('/'):
        return
        
    user_id = event.sender_id
    text = event.raw_text.strip()
    
    if user_id not in user_states:
        return

    action = user_states[user_id].get("action")

    # 1. تفعيل الاشتراك عبر الآيدي (للمشرف فقط)
    if action == "waiting_for_sub" and user_id == ADMIN_ID:
        try:
            parts = text.split()
            if parts[0].upper() == "ID" and parts[-1].lower() == "d":
                target_user_id = int(parts[1])
                days = int(parts[2])
                expiry = add_subscriber(target_user_id, days)
                
                try:
                    await client.send_message(
                        target_user_id, 
                        f"🎉 **تم تفعيل اشتراكك بنجاح!**\n⏳ المدة المضافة: `{days}` أيام\n📅 تاريخ الانتهاء: `{expiry}`"
                    )
                except:
                    pass
                
                await event.respond(f"✅ تم تفعيل الاشتراك للمستخدم `{target_user_id}` لمدة `{days}` أيام بنجاح!")
            else:
                await event.respond("❌ الصيغة خاطئة. استخدم الصيغة: `ID 123456 5 d`")
        except Exception as e:
            await event.respond(f"❌ حدث خطأ في الصياغة: `{str(e)}`")
        user_states.pop(user_id, None)

    # 2. إضافة رقم يدوياً
    elif action == "waiting_for_phone":
        phone_number = text
        user_states[user_id]["phone"] = phone_number
        user_states[user_id]["action"] = "waiting_for_code"
        await event.respond(f"⏳ جاري إرسال كود التحقق (OTP) إلى الرقم `{phone_number}`...")
        try:
            session_name = f"session_{user_id}_{phone_number.replace('+', '')}"
            temp_client = TelegramClient(session_name, API_ID, API_HASH)
            await temp_client.connect()
            sent = await temp_client.send_code_request(phone_number)
            user_states[user_id]["temp_client"] = temp_client
            user_states[user_id]["phone_code_hash"] = sent.phone_code_hash
            await event.respond("✅ **تم إرسال كود التحقق!**\nيرجى إرسال الكود الآن (مثال: `12345`).")
        except Exception as e:
            await event.respond(f"❌ خطأ: `{str(e)}`\nتأكد من صحة الرقم وأعد المحاولة.")
            user_states.pop(user_id, None)

    elif action == "waiting_for_code":
        code = text
        state = user_states[user_id]
        temp_client = state["temp_client"]
        phone = state["phone"]
        phone_code_hash = state["phone_code_hash"]
        try:
            await temp_client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            add_user_number(user_id, phone)
            await temp_client.disconnect()
            await event.respond("🎉 **تم تسجيل الدخول وحفظ الرقم في قائمتك الخاصة بنجاح! ✅**")
            user_states.pop(user_id, None)
        except SessionPasswordNeededError:
            user_states[user_id]["action"] = "waiting_for_password"
            await event.respond("🔒 **الحساب محمي بكلمة مرور (التحقق بخطوتين - 2FA).**\nيرجى إرسال كلمة المرور الآن:")
        except Exception as e:
            await event.respond(f"❌ الكود غير صحيح: `{str(e)}`")

    elif action == "waiting_for_password":
        password = text
        state = user_states[user_id]
        temp_client = state["temp_client"]
        phone = state["phone"]
        try:
            await temp_client.sign_in(password=password)
            add_user_number(user_id, phone)
            await temp_client.disconnect()
            await event.respond("🎉 **تم تخطي التحقق بخطوتين وحفظ الحساب بنجاح تام! 🔒**")
            user_states.pop(user_id, None)
        except Exception as e:
            await event.respond(f"❌ كلمة المرور غير صحيحة: `{str(e)}`")

    # 3. حذف رقم
    elif action == "waiting_for_delete":
        phone_to_delete = text
        delete_user_number(user_id, phone_to_delete)
        await event.respond(f"🗑️ تمت محاولة حذف الرقم `{phone_to_delete}` من قائمتك.")
        user_states.pop(user_id, None)

    # 4. معالجة روابط العمليات الفعليّة (إنضمام، مغادرة، مجلدات، إحالة)
    elif action in ["waiting_for_ref", "waiting_for_join", "waiting_for_leave", "waiting_for_folder"]:
        link = text
        user_numbers_list = get_user_numbers(user_id)
        
        if not user_numbers_list:
            await event.respond("⚠️ لا توجد لديك أي أرقام/حسابات مسجلة لتنفيذ هذه العملية. قم بإضافة أرقامك أو ملفات جلساتك أولاً.")
            user_states.pop(user_id, None)
            return

        await event.respond(f"⏳ جاري تنفيذ العملية على عدد `{len(user_numbers_list)}` من حساباتك المسجلة...")
        
        success_count = 0
        fail_count = 0

        for phone in user_numbers_list:
            try:
                # البحث عن الجلسة الخاصة بالحساب
                session_name = f"session_{user_id}_{phone.replace('+', '')}"
                if not os.path.exists(session_name + ".session"):
                    # البحث في مجلد المستخلصات أو الجلسات العامة
                    session_name = phone.replace('+', '')
                
                async with TelegramClient(session_name, API_ID, API_HASH) as acc:
                    if action == "waiting_for_join":
                        if "+" in link or "joinchat" in link:
                            invite_hash = link.split("/")[-1].replace("+", "")
                            await acc(ImportChatInviteRequest(invite_hash))
                        else:
                            channel_username = link.split("/")[-1].replace("@", "")
                            await acc(JoinChannelRequest(channel_username))
                            
                    elif action == "waiting_for_leave":
                        channel_username = link.split("/")[-1].replace("@", "")
                        await acc(LeaveChannelRequest(channel_username))

                    elif action == "waiting_for_ref":
                        parts = link.split("/")
                        bot_username = parts[-1].split("?")[0].replace("@", "")
                        param = ""
                        if "start=" in link:
                            param = link.split("start=")[1].split("&")[0]
                        await acc(StartBotRequest(bot=bot_username, peer=bot_username, start_param=param))

                    elif action == "waiting_for_folder":
                        if "addlist" in link:
                            slug = link.split("addlist/")[-1]
                            invite = await acc(CheckChatlistInviteRequest(slug=slug))
                            await acc(JoinChatlistInviteRequest(slug=slug, peers=invite.peers))

                    success_count += 1
            except Exception as ex:
                fail_count += 1

        await event.respond(
            f"📊 **نتيجة تنفيذ العملية:**\n\n"
            f"✅ نجحت مع `{success_count}` حساب.\n"
            f"❌ فشلت مع `{fail_count}` حساب.\n"
            f"الرابط المعالج: `{link}`"
        )
        user_states.pop(user_id, None)

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Zack-Bot started successfully with full features.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
