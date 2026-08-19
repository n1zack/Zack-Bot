from telethon import Button

def get_main_keyboard():
    # القائمة الرئيسية المختصرة (خاصة بالجلسات والأرقام فقط)
    buttons = [
        [Button.inline("⚙️ لوحة التحكم والإدارة", b.decode() if isinstance(b, bytes) else "admin_panel")], # للتحكم
        [Button.inline("➕ إضافة رقم", b"add_number"), Button.inline("➖ حذف رقم", b"delete_number")],
        [Button.inline("📂 تسجيل عبر ملف جلسات", b"session_login"), Button.inline("📁 إنشاء ملف جلسات", b"create_session")],
        [Button.inline("🔗 تشغيل عبر رابط إحالة", b"ref_link"), Button.inline("➕ انضمام لقناة/مجموعة", b"join_chat")],
        [Button.inline("➖ مغادرة قناة/مجموعة", b"leave_chat"), Button.inline("📂 انضمام لمجلد قنوات", b"join_folder")],
        [Button.inline("❤️ تفاعل رياكشن", b"send_reaction")]
    ]
    # تصحيح بسيط لضمان توافق الزر الأول
    buttons[0] = [Button.inline("⚙️ لوحة التحكم والإدارة", b"admin_panel")]
    return buttons

def get_admin_panel_keyboard():
    # الأزرار التي ستظهر حصرياً داخل "لوحة التحكم"
    buttons = [
        [Button.inline("📊 الإحصائيات", b"stats"), Button.inline("💎 تفعيل اشتراك (ID)", b"activate_sub")],
        [Button.inline("👥 قائمة المشتركين", b"list_subs"), Button.inline("👤 إدارة المشرفين", b"manage_admins")],
        [Button.inline("📢 الإذاعة والتوجيه", b"broadcast")],
        [Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]
    ]
    return buttons

def get_back_keyboard():
    # زر الرجوع الموحد للبيانات الفرعية
    return [[Button.inline("🔙 رجوع للوحة التحكم", b"admin_panel")]]
