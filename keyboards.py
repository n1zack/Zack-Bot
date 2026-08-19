from telethon import Button

def get_main_keyboard(is_admin=False):
    keyboard = [
        [Button.inline("📱 أرقامي", "my_numbers"), Button.inline("➕ إضافة رقم", "add_number"), Button.inline("➖ حذف رقم", "delete_number")],
        [Button.inline("📥 تسجيل دخول (جلسات متعددة)", "session_login")],
        [Button.inline("🤖 تشغيل بوت (إحالة / Mini App)", "ref_bot")],
        [Button.inline("📢 انضمام لقناة/مجموعة", "join_chat"), Button.inline("🚪 مغادرة قناة/مجموعة", "leave_chat")],
        [Button.inline("📁 انضمام لمجلد", "join_folder")]
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
