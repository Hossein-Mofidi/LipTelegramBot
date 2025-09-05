from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.admin import ADMINS, load_users


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        users = load_users()

        if str(user_id) not in users:
            await update.message.reply_text('برای فعالسازی ربات به ادمین مراجعه کنید')
            return


    keyboard = [
        [InlineKeyboardButton('منوی اصلی', callback_data='main')]
    ]
    await update.message.reply_text(
        'به ربات خوش آمدید!',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )