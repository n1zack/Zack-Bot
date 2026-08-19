from telethon import Button
from telethon import Button

def get_main_keyboard():
    return [
        [Button.inline("⚙️ لوحة التحكم والإدارة", b"admin_panel")],
        [Button.inline("📱 أرقامي (قائمة الأرقام)", b"my_numbers")],
        [Button.inline("➕ إضافة رقم", b"add_number"), Button.inline("➖ حذف رقم", b"delete_number")],
        # تم إضافة زر إنشاء ملف جلسات لجميع الحسابات
        [Button.inline("💾 تصدير/إنشاء ملف جلسات للكل", b"export_all_sessions")],
        [Button.inline("📂 تسجيل جلسة (دعم متعدد)", b"session_login")],
        [Button.inline("🔗 تشغيل بوت/Mini App", b"ref_link"), Button.inline("❤️ تفاعل رياكشن", b"send_reaction")],
        [Button.inline("➕ انضمام لقناة", b"join_chat"), Button.inline("➖ مغادرة قناة", b"leave_chat")],
        [Button.inline("📁 انضمام لمجلد قنوات", b"join_folder")]
    ]


def get_admin_panel_keyboard():
    # أزرار لوحة الإدارة
    return [
        [Button.inline("📊 الإحصائيات", b"stats"), Button.inline("💎 تفعيل اشتراك", b"activate_sub")],
        [Button.inline("👥 قائمة المشتركين", b"list_subs"), Button.inline("👤 إدارة المشرفين", b"manage_admins")],
        [Button.inline("📢 الإذاعة والتوجيه", b"broadcast")],
        [Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]
    ]

def get_back_keyboard():
    # زر الرجوع الموحد
    return [[Button.inline("🔙 رجوع للقائمة الرئيسية", b"back_home")]]
