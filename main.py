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
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
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

# سيرفر الويب لضمان بقاء البوت نشطاً على Render وتجنب السبات
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

# تهيئة عميل التيليجرام الأساسي للبوت مع حماية وتجنب التداخل
client = TelegramClient('zack_bot', API_ID, API_HASH)

# --- أمر /start ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    try:
        user_id = event.sender_id
        user_states.pop(user_id, None)
        is_admin = (user_id == ADMIN_ID)
        
        welcome_text = (
            f"👑 **مرحباً بك يا زاك في لوحة تحكم البوت الشاملة**\n"
            f"معرفك (ID): `{user_id}`\n\n"
            "اختر العملية المطلوبة لإدارة الحسابات والجلسات والأرقام:"
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

        elif data == "my_numbers":
            await event.answer()
            numbers = get_user_numbers(user_id)
            if numbers:
                numbers_list = "\n".join([f"📱 `{num}`" for num in numbers])
                text = f"📱 **أرقامك المسجلة خصيصاً لك:**\n\n{numbers_list}"
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
            await event.edit("➖ **حذف رقم:**\nأرسل الرقم الذي تريد حذفه.", buttons=get_back_keyboard())

        elif data == "session_login":
            await event.answer()
            await event.edit("📥 **تسجيل دخول عبر ملف جلسات:**\nأرسل ملف `zip` أو `sessions` أو `txt` وسأقوم بمعالجته.", buttons=get_back_keyboard())
            
        elif data == "export_sessions":
            await event.answer()
            nums = get_user_numbers(user_id)
            if not nums:
                return await event.edit("⚠️ لا توجد أرقام أو جلسات محفوظة لتصديرها.", buttons=get_back_keyboard())
            
            await event.edit("⏳ جاري تجميع ملفات الجلسات الخاصة بك...")
            zip_filename = f"my_sessions_{user_id}.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for phone in nums:
                    s_name = f"session_{user_id}_{phone.replace('+', '')}.session"
                    if os.path.exists(s_name):
                        zipf.write(s_name)
            
            if os.path.exists(zip_filename):
                await event.respond(file=zip_filename)
                os.remove(zip_filename)
                await event.edit("✅ **تم تصدير ملفات الجلسات بنجاح!**", buttons=get_back_keyboard())
            else:
                await event.edit("❌ لم يتم العثور على ملفات جلسات مادية مرتبطة بأرقامك.", buttons=get_back_keyboard())

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
            await event.edit("❤️ **تفاعل رياكشن:**\nأرسل رابط المنشور في القناة أو المجموعة متبوعاً بالإيموجي (مثال:\n`https://t.me/channel/123 👍`)\nأو أرسل الرابط وسنستخدم تفاعل 👍 افتراضياً.", buttons=get_back_keyboard())

        elif data == "back_home":
            await event.answer()
            user_states.pop(user_id, None)
            is_admin = (user_id == ADMIN_ID)
            await event.edit("👑 **مرحباً بك من جديد يا زاك**\n\nاختر العملية المطلوبة:", buttons=get_main_keyboard(is_admin))
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")

# --- معالجة الملفات المرسلة ---
@client.on(events.NewMessage(func=lambda e: e.file))
async def handle_session_file(event):
    try:
        user_id = event.sender_id
        if user_id != ADMIN_ID and not is_subscribed(user_id):
            return await event.respond("⚠️ عذراً، أنت غير مشترك في البوت.")

        path = await event.download_media()
        filename = event.file.name or ""
        await event.respond("📂 جاري فحص الملف ومعالجة الجلسات...")
        
        success_numbers = []
        
        if filename.endswith('.zip') or path.endswith('.zip'):
            extract_dir = f"sessions_{user_id}"
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith('.session') or file.endswith('.txt'):
                            file_path = os.path.join(root, file)
                            base_n = file.replace('.session', '').replace('.txt', '')
                            sess_name = f"session_{user_id}_{base_n}"
                            try:
                                # نقل وتوحيد التسمية
                                if file_path != f"{sess_name}.session":
                                    import shutil
                                    shutil.copy(file_path, f"{sess_name}.session")
                                
                                sess_client = TelegramClient(sess_name, API_ID, API_HASH)
                                await sess_client.connect()
                                if await sess_client.is_user_authorized():
                                    me = await sess_client.get_me()
                                    if me and me.phone:
                                        p_str = "+" + str(me.phone)
                                        add_user_number(user_id, p_str)
                                        success_numbers.append(p_str)
                                await sess_client.disconnect()
                            except: pass

        if success_numbers:
            await event.respond(f"✅ تمت إضافة الحسابات بنجاح:\n" + "\n".join([f"- `{n}`" for n in success_numbers]))
        else:
            await event.respond("⚠️ لم يتم التعرف على حسابات صالحة داخل الملف المرفق.")

        if os.path.exists(path): os.remove(path)
    except Exception as e:
        logger.error(f"Error handling file: {e}")

# --- معالجة الرسائل النصية وحالات التفاعل ---
@client.on(events.NewMessage(incoming=True))
async def handle_user_messages(event):
    if not event.is_private or event.raw_text.startswith('/'):
        return
        
    user_id = event.sender_id
    text = event.raw_text.strip()
    
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
            user_states.pop(user_id, None)

        elif action == "waiting_for_phone":
            user_states[user_id]["phone"] = text
            user_states[user_id]["action"] = "waiting_for_code"
            session_name = f"session_{user_id}_{text.replace('+', '')}"
            temp_client = TelegramClient(session_name, API_ID, API_HASH)
            await temp_client.connect()
            sent = await temp_client.send_code_request(text)
            user_states[user_id]["temp_client"] = temp_client
            user_states[user_id]["phone_code_hash"] = sent.phone_code_hash
            await event.respond("✅ تم إرسال كود التحقق (OTP). أرسله الآن:")

        elif action == "waiting_for_code":
            state = user_states[user_id]
            await state["temp_client"].sign_in(phone=state["phone"], code=text, phone_code_hash=state["phone_code_hash"])
            add_user_number(user_id, state["phone"])
            await state["temp_client"].disconnect()
            await event.respond("🎉 تم تسجيل الدخول وحفظ الرقم بنجاح!")
            user_states.pop(user_id, None)

        elif action == "waiting_for_password":
            state = user_states[user_id]
            await state["temp_client"].sign_in(password=text)
            add_user_number(user_id, state["phone"])
            await state["temp_client"].disconnect()
            await event.respond("🎉 تم تخطي التحقق بخطوتين وحفظ الحساب بنجاح!")
            user_states.pop(user_id, None)

        elif action == "waiting_for_delete":
            delete_user_number(user_id, text)
            await event.respond(f"🗑️ تمت محاولة حذف الرقم `{text}`.")
            user_states.pop(user_id, None)

        elif action in ["waiting_for_ref", "waiting_for_join", "waiting_for_leave", "waiting_for_folder", "waiting_for_reaction"]:
            link = text.split()[0] # استخراج الرابط إن وجد مع نص إضافي كالإيموجي
            emoji = text.split()[1] if len(text.split()) > 1 else "👍"
            
            nums = get_user_numbers(user_id)
            if not nums:
                await event.respond("⚠️ لا توجد أرقام مسجلة لديك لتنفيذ العملية.")
                user_states.pop(user_id, None)
                return

            await event.respond(f"⏳ جاري التنفيذ على `{len(nums)}` حساب...")
            success, fail = 0, 0

            for phone in nums:
                try:
                    s_name = f"session_{user_id}_{phone.replace('+', '')}"
                    if not os.path.exists(s_name + ".session"):
                        s_name = phone.replace('+', '')
                    
                    async with TelegramClient(s_name, API_ID, API_HASH) as acc:
                        if action == "waiting_for_join":
                            if "+" in link or "joinchat" in link:
                                await acc(ImportChatInviteRequest(link.split("/")[-1].replace("+", "")))
                            else:
                                await acc(JoinChannelRequest(link.split("/")[-1].replace("@", "")))
                        elif action == "waiting_for_leave":
                            await acc(LeaveChannelRequest(link.split("/")[-1].replace("@", "")))
                        elif action == "waiting_for_ref":
                            parts = link.split("/")
                            bot_u = parts[-1].split("?")[0].replace("@", "")
                            param = link.split("start=")[1].split("&")[0] if "start=" in link else ""
                            await acc(StartBotRequest(bot=bot_u, peer=bot_u, start_param=param))
                        elif action == "waiting_for_folder":
                            if "addlist" in link:
                                slug = link.split("addlist/")[-1]
                                invite = await acc(CheckChatlistInviteRequest(slug=slug))
                                await acc(JoinChatlistInviteRequest(slug=slug, peers=invite.peers))
                        elif action == "waiting_for_reaction":
                            # تحليل رابط المنشور (مثال t.me/channel/123)
                            parts = link.split("/")
                            channel_username = parts[-2]
                            msg_id = int(parts[-1])
                            entity = await acc.get_entity(channel_username)
                            await acc(SendReactionRequest(peer=entity, msg_id=msg_id, reaction=[ReactionEmoji(emoticon=emoji)]))

                        success += 1
                except Exception as ex:
                    fail += 1

            await event.respond(f"📊 **النتيجة:**\n✅ نجحت: `{success}`\n❌ فشلت: `{fail}`")
            user_states.pop(user_id, None)
    except Exception as err:
        logger.error(f"Error in message handler: {err}")
        await event.respond(f"❌ حدث خطأ أثناء التنفيذ: `{str(err)}`")
        user_states.pop(user_id, None)

async def main():
    await start_web_server()
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Zack-Bot started successfully with full features.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
 
