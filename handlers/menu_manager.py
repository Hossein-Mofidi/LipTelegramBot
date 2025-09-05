from telegram import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


class MenuManager:
    @staticmethod
    def get_main_menu():
        keyboard = [
            [InlineKeyboardButton('ترکیب رنگ لب', callback_data='color:start')],
            [InlineKeyboardButton('تکنیک لب های چالشی', callback_data='challenge:menu')],
            [InlineKeyboardButton('بیماری های لب و درمان آن', callback_data='treatment:menu')],
            [InlineKeyboardButton('مراقبت ها', callback_data='care:menu')],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_admin_main_menu():
        keyboard = [
            [InlineKeyboardButton('افزودن کاربر', callback_data='admin:add_user')],
            [InlineKeyboardButton('حذف کاربر', callback_data='admin:remove_user')],
            [InlineKeyboardButton('لیست کاربران', callback_data='admin:list_users')],
            [InlineKeyboardButton('پاسخ به سوالات', callback_data='main')],
        ]
        return InlineKeyboardMarkup(keyboard)


async def main_handler(query: CallbackQuery):
    """
    Handle the main menu options.
    """
    if query.data == 'main':
        reply_markup = MenuManager.get_main_menu()

        await query.edit_message_text(
            text='لطفا گزینه موردنظر خود را انتخاب کنید',
            reply_markup=reply_markup
        )
    elif query.data == 'main:admin':
        reply_markup = MenuManager.get_admin_main_menu()

        await query.message.get_bot().send_message(
            text='لطفا گزینه موردنظر خود را انتخاب کنید',
            reply_markup=reply_markup,
            chat_id=query.message.chat.id
        )