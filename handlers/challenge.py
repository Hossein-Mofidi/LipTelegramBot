import json
import logging
import os
from datetime import datetime
from typing import Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from config import ADMINS, ANSWERS, get_photo, BRANDS

logger = logging.getLogger(__name__)

# Available challenges with Persian display text
CHALLENGES = {
    'a': "لب تاتوی قبلی بنفش دارد",
    'b': "لب دو رنگ است",
    'c': "لب دو نوع کبودی دارد",
    'd': "کبودی لب با اندرتون متفاوت است"
}


def create_back_button(target: str) -> InlineKeyboardButton:
    """Create a consistent back button"""
    return InlineKeyboardButton("◀️ بازگشت", callback_data=f"challenge:back:{target}")


def create_edit_button(challenge_id: str, brand: str = None) -> InlineKeyboardButton:
    """Create edit button visible only to admins"""
    if brand:
        return InlineKeyboardButton("✏️ ویرایش", callback_data=f"challenge:edit:{challenge_id}:{brand}")
    return InlineKeyboardButton("✏️ ویرایش", callback_data=f"challenge:edit:{challenge_id}")


async def show_challenges_menu(query, context: ContextTypes.DEFAULT_TYPE):
    """Display the main challenges menu to user"""
    try:
        await query.answer()

        keyboard = [
            [InlineKeyboardButton(text, callback_data=f"challenge:{challenge_id}")]
            for challenge_id, text in CHALLENGES.items()
        ]
        keyboard.append([create_back_button("main")])

        await query.edit_message_text(
            text="مشکل لب چیست؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_challenges_menu: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در نمایش منو")


async def handle_challenge_choice(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user selects a challenge"""
    try:
        await query.answer()
        user_id = query.from_user.id
        challenge_id = query.data.split(':')[1]

        # Store selected challenge in context
        context.user_data['current_challenge'] = challenge_id

        if challenge_id == 'a':  # Purple tattoo case
            await show_brand_selection(query, context, user_id)
        else:
            await show_challenge_solution(query, context, challenge_id, user_id in ADMINS)

    except Exception as e:
        logger.error(f"Error in handle_challenge_choice: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش انتخاب")


async def show_brand_selection(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Show brand selection for purple tattoo case"""
    try:
        keyboard = [
            [InlineKeyboardButton(brand, callback_data=f"challenge:brand:{brand}")]
            for brand in BRANDS
        ]
        keyboard.append([create_back_button("menu")])

        await query.edit_message_text(
            text="برند مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_brand_selection: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در نمایش برندها")


async def handle_brand_selection(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle when user selects a brand"""
    try:
        await query.answer()
        user_id = query.from_user.id
        brand = query.data.split(':')[2]
        challenge_id = context.user_data.get('current_challenge')

        # Store selected brand in context
        context.user_data['current_brand'] = brand

        await show_challenge_solution(query, context, challenge_id, user_id in ADMINS, brand)

    except Exception as e:
        logger.error(f"Error in handle_brand_selection: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش انتخاب برند")


async def show_challenge_solution(query, context, challenge_id, is_admin=False, brand=None):
    """Show the solution for selected challenge"""
    try:
        # Load saved solutions
        solutions = load_challenge_solutions()

        # Get solution based on challenge and brand
        if brand and challenge_id == 'a':
            solution = solutions.get(challenge_id, {}).get(brand, {})
            display_text = f"راهکار برای {CHALLENGES[challenge_id]} با برند {brand}:\n"
        else:
            solution = solutions.get(challenge_id, {})
            display_text = f"راهکار برای {CHALLENGES[challenge_id]}:\n"

        # Prepare keyboard
        keyboard = []
        if is_admin:
            keyboard.append([create_edit_button(challenge_id, brand)])
        keyboard.append([create_back_button("menu")])

        # Get solution text or default message
        text = solution.get('text', display_text + "(هنوز ثبت نشده)")
        photo_path = solution.get('photo')

        # Send photo if available
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

        # Fallback to text only
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Error in show_challenge_solution: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در نمایش راهکار")


async def handle_edit_request(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle when admin requests to edit a solution"""
    try:
        await query.answer()
        parts = query.data.split(':')
        challenge_id = parts[2]
        brand = parts[3] if len(parts) > 3 else None

        # Store editing state in context
        context.user_data['editing_challenge'] = challenge_id
        context.user_data['editing_brand'] = brand
        context.user_data['awaiting_challenge_answer'] = True

        if brand:
            message = f"لطفا متن جدید برای {CHALLENGES[challenge_id]} با برند {brand} را وارد کنید:"
        else:
            message = f"لطفا متن جدید برای {CHALLENGES[challenge_id]} را وارد کنید:"

        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ انصراف", callback_data=f"challenge:{challenge_id}")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in handle_edit_request: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش درخواست ویرایش")


async def handle_challenge_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process new solution text entered by admin"""
    try:
        user_id = update.effective_user.id
        if user_id not in ADMINS or not context.user_data.get('awaiting_challenge_answer'):
            return

        challenge_id = context.user_data.get('editing_challenge')
        brand = context.user_data.get('editing_brand')
        new_text = update.message.text

        # Save the updated solution
        save_challenge_solution(challenge_id, new_text, user_id, brand)

        if brand:
            await update.message.reply_text(
                text=f"✅ پاسخ برای {CHALLENGES[challenge_id]} با برند {brand} با موفقیت به‌روز شد",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("مشاهده پاسخ",
                                          callback_data=f"challenge:brand:{brand}")]
                ])
            )
        else:
            await update.message.reply_text(
                text=f"✅ پاسخ برای {CHALLENGES[challenge_id]} با موفقیت به‌روز شد",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("مشاهده پاسخ",
                                          callback_data=f"challenge:{challenge_id}")]
                ])
            )

        # Clear editing state
        context.user_data.pop('awaiting_challenge_answer', None)
        context.user_data.pop('editing_challenge', None)
        context.user_data.pop('editing_brand', None)

    except Exception as e:
        logger.error(f"Error in handle_challenge_text_input: {e}", exc_info=True)
        await update.message.reply_text("⚠️ خطا در ذخیره پاسخ")


def load_challenge_solutions() -> Dict:
    """Load challenge solutions from JSON file"""
    try:
        if not os.path.exists(ANSWERS):
            return {}

        with open(ANSWERS, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('challenges', {})

    except Exception as e:
        logger.error(f"Error loading challenge solutions: {e}", exc_info=True)
        return {}


def save_challenge_solution(challenge_id: str, text: str, user_id: int, brand: str = None):
    """Save or update a challenge solution"""
    try:
        # Load existing data
        if os.path.exists(ANSWERS):
            with open(ANSWERS, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        # Initialize challenges section if needed
        if 'challenges' not in data:
            data['challenges'] = {}

        # For brand-specific solutions (purple tattoo)
        if brand and challenge_id == 'a':
            if challenge_id not in data['challenges']:
                data['challenges'][challenge_id] = {}

            data['challenges'][challenge_id][brand] = {
                'text': text,
                'updated_at': datetime.now().isoformat(),
                'updated_by': user_id
            }
        else:
            # For regular solutions
            data['challenges'][challenge_id] = {
                'text': text,
                'updated_at': datetime.now().isoformat(),
                'updated_by': user_id
            }

        # Save back to file
        with open(ANSWERS, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"Error saving challenge solution: {e}", exc_info=True)
        raise


async def handle_challenge_answer(query, context: ContextTypes.DEFAULT_TYPE):
    """Main callback handler for challenge-related actions"""
    try:
        await query.answer()
        data = query.data.split(':')

        if data[1] == 'menu':
            await show_challenges_menu(query, context)
        elif data[1] in CHALLENGES.keys():
            await handle_challenge_choice(query, context)
        elif data[1] == 'brand':
            await handle_brand_selection(query, context)
        elif data[1] == 'edit':
            await handle_edit_request(query, context)
        elif data[1] == 'back':
            target = data[2]
            if target == 'main':
                from .menu_manager import main_handler
                await main_handler(query)
            else:
                await show_challenges_menu(query, context)

    except Exception as e:
        logger.error(f"Error in challenge_callback_handler: {e}", exc_info=True)
        await query.edit_message_text("⚠️ خطا در پردازش درخواست")