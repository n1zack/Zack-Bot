import os
from pyrogram import filters
from database import add_phone, get_user_phones, delete_phone_by_id
from keyboards import my_numbers_keyboard, back_keyboard

async def handle_session_file(client, message):
    if message.document:
        file_name = message.document.file_name
        if file_name.endswith(('.zip', '.txt', '.session')):
            user_folder = f"sessions/{message.from_user.id}"
            os.makedirs(user_folder, exist_ok=True)
            await message.download(file_path=f"{user_folder}/{file_name}")
            await message.reply("✅ تم رفع وحفظ ملف الجلسة بنجاح!", reply_markup=back_keyboard())
        else:
            await message.reply("❌ نوع الملف غير مدعوم.", reply_markup=back_keyboard())
