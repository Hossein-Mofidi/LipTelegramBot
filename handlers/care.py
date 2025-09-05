import json
import logging
import os
from datetime import datetime
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from config import ADMINS, ANSWERS

logger = logging.getLogger(__name__)

# Care options with their Persian names
CARE_OPTIONS = {
    "pre_care": "مراقبت قبل از کار",
    "post_care": "مراقبت بعد از کار"
}


def create_back_button(target: str) -> InlineKeyboardButton:
    """Create a consistent back button"""
    return InlineKeyboardButton("◀️ بازگشت", callback_data=f"care:back:{target}")


def create_edit_button(care_type: str) -> InlineKeyboardButton:
    """Create an edit button for admin"""
    return InlineKeyboardButton("✏️ ویرایش", callback_data=f"care:edit:{care_type}")


async def show_care_menu(query, context: ContextTypes.DEFAULT_TYPE):
    """Show the main care options menu"""
    try:
        await query.answer()

        keyboard = [
            [InlineKeyboardButton(text, callback_data=f"care:{care_type}")]
            for care_type, text in CARE_OPTIONS.items()
        ]
        keyboard.append([create_back_button("main")])

        await query.edit_message_text(
            text="نوع مراقبت مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_care_menu: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در نمایش منو")


async def handle_care_choice(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's care type selection"""
    try:
        await query.answer()
        user_id = query.from_user.id
        is_admin = user_id in ADMINS
        care_type = query.data.split(':')[1]

        # Store selected care type in context
        context.user_data['care_type'] = care_type

        await show_care_instructions(query, context, care_type, is_admin)

    except Exception as e:
        logger.error(f"Error in handle_care_choice: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش انتخاب")


async def show_care_instructions(query, context, care_type, is_admin=False):
    """Show care instructions for selected type"""
    try:
        # Load saved instructions
        instructions = load_care_instructions()
        care_data = instructions.get(care_type, {})

        # Prepare keyboard
        keyboard = []
        if is_admin:
            keyboard.append([create_edit_button(care_type)])
        keyboard.append([create_back_button("menu")])

        # Show existing instructions if available
        text = care_data.get('text', f"دستورالعمل {CARE_OPTIONS[care_type]}:\n(هنوز ثبت نشده)")

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error in show_care_instructions: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در نمایش دستورالعمل")


async def handle_edit_request(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin's request to edit care instructions"""
    try:
        await query.answer()
        care_type = query.data.split(':')[2]

        # Store care type in context
        context.user_data['care_type'] = care_type
        context.user_data['awaiting_care_instructions'] = True

        await query.edit_message_text(
            text=f"لطفا متن جدید برای {CARE_OPTIONS[care_type]} را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ انصراف", callback_data=f"care:{care_type}")]
            ])
        )

    except Exception as e:
        logger.error(f"Error in handle_edit_request: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش درخواست ویرایش")


async def handle_care_instructions_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process admin's care instructions input (new or edit)"""
    try:
        user_id = update.effective_user.id

        instructions_text = update.message.text
        care_type = context.user_data.get('care_type')

        # Save instructions to file
        save_care_instructions(care_type, instructions_text, user_id)

        await update.message.reply_text(
            text=f"✅ دستورالعمل {CARE_OPTIONS[care_type]} با موفقیت ذخیره شد",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("مشاهده دستورالعمل", callback_data=f"care:{care_type}")]
            ])
        )

        # Clear state
        context.user_data.pop('awaiting_care_instructions', None)
        context.user_data.pop('care_type', None)

    except Exception as e:
        logger.error(f"Error in handle_care_instructions_input: {e}", exc_info=True)
        await update.message.reply_text("⚠️ خطا در ذخیره دستورالعمل")


def load_care_instructions() -> Dict:
    """Load care instructions from file"""
    try:
        if not os.path.exists(ANSWERS):
            return {}

        with open(ANSWERS, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('care_instructions', {})

    except Exception as e:
        logger.error(f"Error loading care instructions: {e}", exc_info=True)
        return {}


def save_care_instructions(care_type: str, instructions: str, user_id: int):
    """Save new or updated care instructions"""
    try:
        # Load all existing instructions
        if os.path.exists(ANSWERS):
            with open(ANSWERS, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        # Initialize care_instructions section if not exists
        if 'care_instructions' not in data:
            data['care_instructions'] = {}

        # Update or create instructions
        data['care_instructions'][care_type] = {
            'text': instructions,
            'updated_at': datetime.now().isoformat(),
            'updated_by': user_id
        }

        # Save to file
        with open(ANSWERS, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"Error saving care instructions: {e}", exc_info=True)
        raise


async def care_callback_handler(query, context: ContextTypes.DEFAULT_TYPE):
    """Main handler for care-related callbacks"""
    try:
        await query.answer()
        data = query.data.split(':')

        if data[1] == 'menu':
            await show_care_menu(query, context)
        elif data[1] in CARE_OPTIONS.keys():
            await handle_care_choice(query, context)
        elif data[1] == 'edit':
            await handle_edit_request(query, context)
        elif data[1] == 'back':
            target = data[2]
            if target == 'main':
                from .menu_manager import main_handler
                await main_handler(query)
            else:
                await show_care_menu(query, context)

    except Exception as e:
        logger.error(f"Error in care_callback_handler: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش درخواست")