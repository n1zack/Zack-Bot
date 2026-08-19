import logging
from pyrogram import Client, filters
import config
from database import init_db
from keyboards import main_keyboard, back_keyboard
from handlers.user_actions import handle_session_file
from handlers.callbacks import handle_callback_query

logging.basicConfig(level=logging.INFO)

# تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

app = Client(
    "SuperAdminBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    is_admin = (user_id == config.ADMIN_ID)
    await message.reply_text(
        f"مرحباً بك يا {message.from_user.first_name}.\nالبوت جاهز ويعمل بكفاءة تامة ومعلوماتك منعزلة بأمان.",
        reply_markup=main_keyboard(is_admin)
    )

@app.on_message(filters.document)
async def document_handler(client, message):
    await handle_session_file(client, message)

@app.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "home":
        is_admin = (user_id == config.ADMIN_ID)
        await callback_query.message.edit_text("القائمة الرئيسية:", reply_markup=main_keyboard(is_admin))
    elif data == "admin_panel":
        if user_id == config.ADMIN_ID:
            from keyboards import admin_keyboard
            await callback_query.message.edit_text("لوحة التحكم الخاصة بك:", reply_markup=admin_keyboard())
        else:
            await callback_query.answer("عذراً، هذه اللوحة مخصصة للآدمن فقط!", show_alert=True)
    elif data == "my_numbers":
        from database import get_user_phones
        from keyboards import my_numbers_keyboard
        phones = get_user_phones(user_id)
        if not phones:
            await callback_query.message.edit_text("ليس لديك أي أرقام مسجلة.", reply_markup=back_keyboard())
        else:
            await callback_query.message.edit_text("أرقامك المسجلة (اضغط على الزر للحذف الفوري):", reply_markup=my_numbers_keyboard(phones))
    elif data.startswith("del_phone_"):
        from database import delete_phone_by_id, get_user_phones
        from keyboards import my_numbers_keyboard
        phone_id = int(data.split("_")[2])
        delete_phone_by_id(phone_id, user_id)
        phones = get_user_phones(user_id)
        await callback_query.answer("تم حذف الرقم بنجاح!", show_alert=True)
        if not phones:
            await callback_query.message.edit_text("ليس لديك أي أرقام مسجلة.", reply_markup=back_keyboard())
        else:
            await callback_query.message.edit_text("أرقامك المسجلة:", reply_markup=my_numbers_keyboard(phones))
    else:
        await callback_query.answer("تم النقر بنجاح", show_alert=False)

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
