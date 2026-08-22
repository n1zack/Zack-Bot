# ملف النصوص والترجمات (langs.py)

TRANSLATIONS = {
    'ar': {
        'admin_welcome': "👑 **مرحباً بك مجدداً يا زاك (المشرف العام)**\nمعرفك الشخصي (ID): `{user_id}`\n\nاختر العملية المطلوبة من القائمة أدناه:",
        'user_welcome': "👋 **مرحباً بك {user_name}**\nمعرفك الشخصي (ID): `{user_id}`\n\nاختر العملية المطلوبة من القائمة أدناه:",
        'not_subscribed': "⚠️ **أنت غير مشترك في البوت.**\nمعرفك (ID): `{user_id}`\nقم بالتواصل مع @n1zack لتفعيل اشتراكك.",
        
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
        'lang_changed': "✅ تم تغيير اللغة بنجاح!",
        'no_numbers': "⚠️ لا توجد أرقام مسجلة لديك حالياً.",
        'my_numbers_title': "📱 **أرقامك المسجلة في القاعدة السحابية:**\n\n",
        'add_phone_prompt': "➕ **إضافة رقم جديد:**\nأرسل رقم الهاتف بالصيغة الدولية الكاملة (مثال: `+961...`)",
        'admin_panel_title': "⚙️ **Super Admin Control Panel:**\nChoose an appropriate action:",
    },
    'en': {
        'admin_welcome': "👑 **Welcome back Zack (Super Admin)**\nYour ID: `{user_id}`\n\nChoose the required operation from the menu below:",
        'user_welcome': "👋 **Welcome {user_name}**\nYour ID: `{user_id}`\n\nChoose the required operation from the menu below:",
        'not_subscribed': "⚠️ **You are not subscribed to the bot.**\nYour ID: `{user_id}`\nPlease contact @n1zack to activate your subscription.",
        
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
        'lang_changed': "✅ Language changed successfully!",
        'no_numbers': "⚠️ You have no numbers registered currently.",
        'my_numbers_title': "📱 **Your registered numbers in cloud database:**\n\n",
        'add_phone_prompt': "➕ **Add new number:**\nSend the phone number in full international format (e.g., `+961...`)",
        'admin_panel_title': "⚙️ **Super Admin Control Panel:**\nChoose an appropriate action:",
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
