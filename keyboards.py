from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_keyboard(is_admin):
    buttons = [
        [InlineKeyboardButton("إضافة رقم", callback_data="add_num"), InlineKeyboardButton("أرقامي", callback_data="my_numbers")],
        [InlineKeyboardButton("تسجيل جلسة", callback_data="reg_session"), InlineKeyboardButton("إنشاء جلسة", callback_data="create_session")],
        [InlineKeyboardButton("انضمام لمجلد", callback_data="join_folder"), InlineKeyboardButton("انضمام لقناة", callback_data="join_channel")],
        [InlineKeyboardButton("تشغيل بوت", callback_data="run_bot"), InlineKeyboardButton("تفاعل", callback_data="react")],
        [InlineKeyboardButton("مغادرة قناة", callback_data="leave_channel")]
    ]
    if is_admin:
        buttons.insert(0, [InlineKeyboardButton("لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تفعيل اشتراك", callback_data="sub_act"), InlineKeyboardButton("المشتركين", callback_data="subs_list")],
        [InlineKeyboardButton("إرسال لمستخدم", callback_data="send_user"), InlineKeyboardButton("إرسال للكل", callback_data="send_all")],
        [InlineKeyboardButton("الإحصائيات", callback_data="stats"), InlineKeyboardButton("العودة للرئيسية", callback_data="home")]
    ])

def my_numbers_keyboard(user_phones):
    buttons = []
    for row in user_phones:
        buttons.append([InlineKeyboardButton(f"حذف: {row[1]}", callback_data=f"del_phone_{row[0]}")])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="home")])
    return InlineKeyboardMarkup(buttons)

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="home")]
    ])
