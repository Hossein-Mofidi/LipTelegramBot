import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import ContextTypes

from config import ADMINS


# functions for load and save users in files
def save_users(users: list):
    """
    save list of users
    """
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False)


def load_users() -> list:
    """
    load list of users from file
    :return: list of user
    """
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /admin command and send admin options.
    """
    user_id = update.effective_user.id

    if user_id not in ADMINS:
        return

    keyboard = [
        [InlineKeyboardButton('افزودن کاربر', callback_data='admin:add_user')],
        [InlineKeyboardButton('حذف کاربر', callback_data='admin:remove_user')],
        [InlineKeyboardButton('لیست کاربران', callback_data='admin:list_users')],
        [InlineKeyboardButton('پاسخ به سوالات', callback_data='main')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('لطفا گزینه موردنظر خود را انتخاب کنید', reply_markup=reply_markup)


async def admin_handlers(query, update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user commands from the admin menu.
    """
    commands = query.data.split(':')

    if commands[0] != 'admin':
        return

    command = commands[1]

    if command == 'add_user':
        await add_user(query, context)
    elif command == 'remove_user':
        await remove_user(query, context)
    elif command == 'list_users':
        await list_users(update, context)


async def add_user(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the add user command.
    """
    await query.edit_message_text(
        text="لطفا شناسه کاربری (User ID) را برای افزودن ارسال کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ انصراف", callback_data="main:admin"),
            ]
        ])
    )

    # save status for awaiting user ID
    context.user_data['awaiting_user_id'] = True
    context.user_data['action'] = 'add_user'


async def remove_user(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the remove user command.
    """
    await query.edit_message_text(
        text="لطفا شناسه کاربری (User ID) را برای حذف ارسال کنید:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ انصراف", callback_data="main:admin"),
            ]
        ])
    )

    context.user_data['awaiting_user_id'] = True
    context.user_data['action'] = 'remove_user'


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the list users command.
    """
    users = load_users()
    if len(users) == 0:
        await update.get_bot().send_message(
            text="شما هیچ کاربری را به ربات اضافه نکرده اید.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("◀️ بازگشت", callback_data="main:admin"),
                ]
            ]),
            chat_id=update.effective_user.id
        )
        return

    await update.get_bot().send_message(text=f"لیست کاربران " + "\n", chat_id=update.effective_user.id)

    for user in users:
        await update.get_bot().send_message(text=f"{user}\n", chat_id=update.effective_user.id)

    await update.get_bot().send_message(
        text=f"{len(users)}کاربر ",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("◀️ بازگشت", callback_data="main:admin"),
            ]
        ]),
        chat_id=update.effective_user.id
    )


async def handle_userid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user replies.
    """
    user_id = update.message.text

    if not user_id.isdigit():
        await update.message.reply_text(
            text="⚠️ شناسه کاربر باید یک عدد باشد!",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="main:admin"),
                ]
            ])
        )
        return

    if not user_id.isdigit() or not (100000 <= int(user_id) <= 9999999999):
        await update.message.reply_text(
            text="⚠️ شناسه کاربر نامعتبر است!",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ انصراف", callback_data="main:admin"),
                ]
            ])
        )
        return

    if context.user_data['action'] == 'add_user':
        users = load_users()

        # Check if user already exists
        if user_id in users:
            await update.message.reply_text(
                text="کاربر از قبل وجود دارد.⚠️",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("◀️ بازگشت", callback_data="main:admin"),
                    ]
                ])
            )
        else:
            users.append(user_id)
            save_users(users)
            await update.message.reply_text(
                text=f"کاربر با شناسه {user_id} اضافه شد.✅",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("◀️ بازگشت", callback_data="main:admin"),
                    ]
                ])
            )

    elif context.user_data['action'] == 'remove_user':
        users = load_users()

        if user_id in users:
            users.remove(user_id)
            save_users(users)

            await update.message.reply_text(
                text="کاربر با موفقیت حذف شد.✅",
                reply_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("◀️ بازگشت", callback_data="main:admin"),
                    ]
                ])
            )
        else:
            await update.message.reply_text(
                text="کاربر وجود ندارد.⚠️",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("◀️ بازگشت", callback_data="main:admin"),
                    ]
                ])
            )

    # Reset status
    context.user_data.clear()