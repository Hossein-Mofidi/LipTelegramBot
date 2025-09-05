import json
import logging
import os
from datetime import datetime
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from config import ADMINS, ANSWERS, get_photo

logger = logging.getLogger(__name__)

# Treatment options with their Persian names
TREATMENT_OPTIONS = {
    "hypopigmentation": "هایپوپیگمنتیشن لب",
    "hyperpigmentation": "هایپرپیگمنتیشن لب",
    "fordyce": "فوردایس",
    "herpes": "تبخال",
    "lip_gel": "ژل لب"
}

# Default treatment solutions structure
DEFAULT_TREATMENT_SOLUTIONS = {
    "hypopigmentation": {},
    "hyperpigmentation": {},
    "fordyce": {},
    "herpes": {},
    "lip_gel": {}
}


def create_back_button(target: str) -> InlineKeyboardButton:
    """Create a consistent back button"""
    return InlineKeyboardButton("◀️ بازگشت", callback_data=f"treatment:back:{target}")

def create_edit_button(condition: str) -> InlineKeyboardButton:
    """Create an edit button for admin"""
    return InlineKeyboardButton("✏️ ویرایش", callback_data=f"treatment:edit:{condition}")


async def show_treatment_menu(query, context: ContextTypes.DEFAULT_TYPE):
    """Show the main treatment options menu"""
    try:
        await query.answer()

        keyboard = [
            [InlineKeyboardButton(text, callback_data=f"treatment:{condition}")]
            for condition, text in TREATMENT_OPTIONS.items()
        ]
        keyboard.append([create_back_button("main")])

        await query.edit_message_text(
            text="بیماری مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_treatment_menu: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در نمایش منو")


async def handle_treatment_choice(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's treatment choice"""
    try:
        await query.answer()
        user_id = query.from_user.id
        is_admin = user_id in ADMINS
        condition = query.data.split(':')[1]

        # Store selected condition in context
        context.user_data['treatment_condition'] = condition

        await show_treatment_solution(query, context, condition, is_admin)

    except Exception as e:
        logger.error(f"Error in handle_treatment_choice: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش انتخاب")


async def show_treatment_solution(query, context, condition, is_admin=False):
    """Show treatment solution for selected condition"""
    try:
        # Load saved solutions
        solutions = load_treatment_solutions()
        solution = solutions.get(condition, {})

        # Prepare keyboard
        keyboard = []
        if is_admin:
            keyboard.append([create_edit_button(condition)])
        keyboard.append([create_back_button("menu")])

        # Show existing solution if available
        text = solution.get('text', f"راهکار درمانی برای {TREATMENT_OPTIONS[condition]}:\n(هنوز ثبت نشده)")
        photo_path = solution.get('photo')

        # Send photo if exists
        if photo_path:
            with get_photo(photo_path) as photo_file:
                if photo_file:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=photo_file,
                        caption=text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return

        # Fallback to text only if photo not available
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error in show_treatment_solution: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در نمایش راهکار")


async def handle_treatment_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process admin's treatment solution input (new or edit)"""
    try:
        user_id = update.effective_user.id
        if user_id not in ADMINS or not context.user_data.get('awaiting_treatment_solution'):
            return

        solution_text = update.message.text
        condition = context.user_data.get('treatment_condition')

        # Save solution to file
        save_treatment_solution(condition, solution_text, user_id)

        await update.message.reply_text(
            text=f"✅ راهکار برای {TREATMENT_OPTIONS[condition]} با موفقیت ذخیره شد",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("مشاهده راهکار", callback_data=f"treatment:{condition}")]
            ])
        )

        # Clear state
        context.user_data.pop('awaiting_treatment_solution', None)
        context.user_data.pop('treatment_condition', None)

    except Exception as e:
        logger.error(f"Error in handle_treatment_solution_input: {e}", exc_info=True)
        await update.message.reply_text("⚠️ خطا در ذخیره راهکار")


async def handle_edit_request(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin's request to edit a treatment solution"""
    try:
        await query.answer()
        condition = query.data.split(':')[2]

        # Store condition in context
        context.user_data['treatment_condition'] = condition
        context.user_data['awaiting_treatment_solution'] = True

        await query.edit_message_text(
            text=f"لطفا راهکار جدید برای {TREATMENT_OPTIONS[condition]} را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ انصراف", callback_data=f"treatment:{condition}")]
            ])
        )

    except Exception as e:
        logger.error(f"Error in handle_edit_request: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش درخواست ویرایش")


def load_treatment_solutions() -> Dict:
    """Load treatment solutions from file"""
    try:
        if not os.path.exists(ANSWERS):
            return DEFAULT_TREATMENT_SOLUTIONS

        with open(ANSWERS, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('treatments', DEFAULT_TREATMENT_SOLUTIONS)

    except Exception as e:
        logger.error(f"Error loading treatment solutions: {e}", exc_info=True)
        return DEFAULT_TREATMENT_SOLUTIONS


def save_treatment_solution(condition: str, solution: str, user_id: int):
    """Save new treatment solution"""
    try:
        # Load all existing solutions
        if os.path.exists(ANSWERS):
            with open(ANSWERS, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        # Initialize structure if not exists
        if 'treatments' not in data:
            data['treatments'] = DEFAULT_TREATMENT_SOLUTIONS

        # Store new solution
        data['treatments'][condition] = {
            'text': solution,
            'created_at': datetime.now().isoformat(),
            'created_by': user_id
        }

        # Save to file
        with open(ANSWERS, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"Error saving treatment solution: {e}", exc_info=True)
        raise


async def treatment_callback_handler(query, context: ContextTypes.DEFAULT_TYPE):
    """Main handler for treatment-related callbacks"""
    try:
        await query.answer()
        data = query.data.split(':')

        if data[1] == 'menu':
            await show_treatment_menu(query, context)
        elif data[1] in TREATMENT_OPTIONS.keys():
            await handle_treatment_choice(query, context)
        elif data[1] == 'edit':
            await handle_edit_request(query, context)
        elif data[1] == 'back':
            target = data[2]
            if target == 'main':
                from .menu_manager import main_handler
                await main_handler(query)
            else:
                await show_treatment_menu(query, context)

    except Exception as e:
        logger.error(f"Error in treatment_callback_handler: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش درخواست")