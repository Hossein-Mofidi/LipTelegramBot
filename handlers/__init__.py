from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes, CallbackQueryHandler, filters, MessageHandler, \
    CallbackContext

from config import ADMINS
from .care import care_callback_handler, handle_care_instructions_input
from .challenge import handle_challenge_answer, handle_challenge_answer, handle_challenge_text_input
from .color import color_callback_handler, handle_color_answer
from .menu_manager import main_handler
from .start import start_handler
from .admin import admin_handler, admin_handlers, handle_userid_input
from .treatment import treatment_callback_handler, handle_treatment_answer


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the callback queries.
    """
    query = update.callback_query
    await query.answer()

    if query.data.startswith('main'):
        await main_handler(query)
    elif query.data.startswith('admin'):
        await admin_handlers(query, update, context)
    elif query.data.startswith('color'):
        await color_callback_handler(update, context)
    elif query.data.startswith('challenge'):
        await handle_challenge_answer(query, context)
    elif query.data.startswith('treatment'):
        await treatment_callback_handler(query, context)
    elif query.data.startswith('care'):
        await care_callback_handler(query, context)


async def handle_replies(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return

    if context.user_data.get('awaiting_user_id'):
        await handle_userid_input(update, context)
    elif context.user_data.get('awaiting_challenge_answer'):
        await handle_challenge_text_input(update, context)
    elif context.user_data.get('color_info'):
        await handle_color_answer(update, context)
    elif context.user_data.get('treatment_condition'):
        await handle_treatment_answer(update, context)
    elif context.user_data.get('awaiting_care_instructions'):
        await handle_care_instructions_input(update, context)


def setup_handlers(app: Application):
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('admin', admin_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_replies))