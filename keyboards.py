from telethon import Button

def get_main_keyboard():
    return [
        # الصف الأول: لوحة التحكم
        [Button.inline("⚙️ لوحة التحكم والإدارة", b"admin_panel")],
        
        # الصف الثاني: عرض الأرقام
        [Button.inline("📱 أرقامي (قائمة الأرقام)", b"my_numbers")],
        
        # الصف الثالث: إضافة وحذف الأرقام
        [Button.inline("➕ إضافة رقم", b"add_number"), Button.inline("➖ حذف رقم", b"delete_number")],
        
        # الصف الرابع: تسجيل الجلسات
        [Button.inline("📂 تسجيل جلسة (Zip/Txt/Session)", b"session_login")],
        
        # الصف الخامس: تشغيل الروابط وتفاعل الرياضكشن
        [Button.inline("🔗 تشغيل بوت/Mini App", b"ref_link"), Button.inline("❤️ تفاعل رياكشن", b"send_reaction")],
        
        # الصف السادس: الانضمام والمغادرة والمجلدات
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
