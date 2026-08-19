from telethon import Button

def get_main_keyboard():
    # القائمة الرئيسية الشاملة للـ Super Admin
    buttons = [
        [Button.inline("⚙️ لوحة التحكم", b"admin_panel"), Button.inline("📊 الإحصائيات", b"stats")],
        [Button.inline("➕ إضافة رقم", b"add_number"), Button.inline("➖ حذف رقم", b"delete_number")],
        [Button.inline("📂 تسجيل عبر ملف جلسات", b"session_login"), Button.inline("📁 إنشاء ملف جلسات", b"create_session")],
        [Button.inline("🔗 تشغيل عبر رابط إحالة", b"ref_link"), Button.inline("➕ انضمام لقناة/مجموعة", b"join_chat")],
        [Button.inline("➖ مغادرة قناة/مجموعة", b"leave_chat"), Button.inline("📂 انضمام لمجلد قنوات", b"join_folder")],
        [Button.inline("❤️ تفاعل رياكشن", b"send_reaction"), Button.inline("💎 تفعيل اشتراك (ID)", b"activate_sub")],
        [Button.inline("👥 قائمة المشتركين", b"list_subs"), Button.inline("👤 إدارة المشرفين", b"manage_admins")],
        [Button.inline("📢 الإذاعة والتوجيه", b"broadcast")]
    ]
    return buttons

def get_back_keyboard():
    # زر الرجوع الثابت لأي قائمة فرعية
    return [[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]]
