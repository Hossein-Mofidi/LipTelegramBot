import json
import os
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import ContextTypes
from typing import Dict

from config import ANSWERS, UNDERTONES, BRANDS
from handlers.admin import ADMINS


def create_back_button(target: str) -> InlineKeyboardButton:
    """Helper function to create consistent back buttons"""
    return InlineKeyboardButton("◀️ بازگشت", callback_data=f"color:back:{target}")


async def start_color_selection(query, context: ContextTypes.DEFAULT_TYPE):
    """Initial step - asks if lips have discoloration"""
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("✅", callback_data="color:has_burn"),
            InlineKeyboardButton("❎", callback_data="color:no_burn")
        ],
        [
            InlineKeyboardButton("◀️ بازگشت", callback_data="main")
        ]  # Back to main menu
    ]
    await query.edit_message_text(
        text="لب مشتری شما کبود است؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_burn_type(query, context: ContextTypes.DEFAULT_TYPE):
    """Handles selection of discoloration type"""
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("کبودی بنفش", callback_data="color:purple"),
            InlineKeyboardButton("کبودی قهوه‌ای", callback_data="color:brown"),
            InlineKeyboardButton("کبودی خاکستری", callback_data="color:gray")
        ],
        [create_back_button("color_start")]  # Back to initial question
    ]
    await query.edit_message_text(
        text="رنگ کبودی؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_burn_intensity(query, context: ContextTypes.DEFAULT_TYPE):
    """Handles intensity selection with sample photos"""
    await query.answer()
    burn_type = query.data.split(':')[1]
    context.user_data[query.from_user.id] = {'burn_type': burn_type}

    # # Send sample photos
    # media_group = [
    #     InputMediaPhoto(PHOTOS['intensity']['low'], caption="کم"),
    #     InputMediaPhoto(PHOTOS['intensity']['medium'], caption="متوسط"),
    #     InputMediaPhoto(PHOTOS['intensity']['high'], caption="زیاد")
    # ]
    # await context.bot.send_media_group(
    #     chat_id=query.message.chat.id,
    #     media=media_group
    # )

    keyboard = [
        [
            InlineKeyboardButton("کم", callback_data="color:intensity:low"),
            InlineKeyboardButton("متوسط", callback_data="color:intensity:medium"),
            InlineKeyboardButton("زیاد", callback_data="color:intensity:high")
        ],
        [create_back_button("burn_type")]  # Back to discoloration type
    ]
    await query.edit_message_text(
        text="میزان کبودی لب؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_undertone(query, context: ContextTypes.DEFAULT_TYPE):
    """Handles undertone selection for no-discoloration case"""
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(ut, callback_data=f"color:undertone:{ut}")]
        for ut in UNDERTONES
    ]
    keyboard.append([create_back_button("color_start")])  # Back to initial question
    await query.edit_message_text(
        text="آندرتون لب چیست؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_brand_selection(query, context: ContextTypes.DEFAULT_TYPE):
    """Handles brand selection"""
    await query.answer()
    user_id = query.from_user.id

    # Initialize user data if not exists
    if user_id not in context.user_data:
        context.user_data[user_id] = {}

    # Store selection based on path
    if 'undertone' in query.data:
        context.user_data[user_id]['undertone'] = query.data.split(':')[2]
    elif 'intensity' in query.data:
        context.user_data[user_id]['intensity'] = query.data.split(':')[2]

    keyboard = [
        [InlineKeyboardButton(brand, callback_data=f"color:brand:{brand}")]
        for brand in BRANDS
    ]

    # Dynamic back button based on path
    back_target = "undertone" if 'undertone' in context.user_data[user_id] else "intensity"
    keyboard.append([create_back_button(back_target)])

    await query.edit_message_text(
        text="ترکیب رنگ با چه برندی می‌خواهید؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_final_result(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Send final color combination result
    - For admins: Allows saving new combinations
    - For regular users: Shows existing combinations from file
    """
    await query.answer()
    user_id = query.from_user.id
    is_admin = user_id in ADMINS  # Check if user is admin

    # Get user's selection data
    user_info = context.user_data.get(user_id, {})
    if not user_info:
        await query.message.reply_text(
            text="⚠️ خطا در پردازش اطلاعات",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بازگشت به ابتدا", callback_data="color:start")]  # "Restart selection"
            ])
        )
        return

    brand = query.data.split(':')[2]
    user_info['brand'] = brand

    if is_admin:
        # ADMIN FLOW: Get and save new combination
        await query.edit_message_text(
            text=f"ترکیب با برند {brand} را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ انصراف", callback_data="color:back_to_brands")]
            ])
        )

        # Set state to wait for combination input
        context.user_data['answer_color'] = True
        context.user_data['color_info'] = user_info
        return

    else:
        # REGULAR USER FLOW: Read existing combination
        try:
            if not os.path.exists(ANSWERS):
                raise FileNotFoundError

            # Load existing combinations
            with open(ANSWERS, 'r', encoding='utf-8') as f:
                combinations = json.load(f)

            # Generate unique key for this combination
            combo_key = None
            if 'burn_type' in user_info:
                # For discolored lips: burnType_intensity_brand
                combo_key = f"{user_info['burn_type']}_{user_info['intensity']}_{brand}"
            else:
                # For normal lips: undertone_brand
                combo_key = f"{user_info['undertone']}_{brand}"

            combination = combinations.get(combo_key)

            if not combination:
                await query.edit_message_text(
                    text="⚠️ ترکیب برای این مشخصات یافت نشد",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ بازگشت", callback_data="color:back_to_brands")]
                    ])
                )
                return

            # Format result message
            text = (
                f"ترکیب رنگ پیشنهادی:\n"  # "Recommended color combination:"
                f"• {'نوع کبودی: ' + user_info['burn_type'] if 'burn_type' in user_info else 'آندرتون: ' + user_info['undertone']}\n"
                f"• {'شدت کبودی: ' + user_info['intensity'] if 'intensity' in user_info else ''}\n"
                f"• برند: {brand}\n\n"  # "Brand:"
                f"🔹 ترکیب نهایی:\n{combination['formula']}\n\n"
                f"📝 نکات: {combination.get('notes', '')}"
            )

            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 انتخاب مجدد", callback_data="color:start")]  # "Restart selection"
                ])
            )

        except Exception as e:
            print(f"Error: {e}")
            await query.edit_message_text(
                text="⚠️ خطا در دریافت اطلاعات ترکیب",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ بازگشت", callback_data="main:menu")]
                ])
            )
        finally:
            context.user_data.pop(user_id, None)


async def handle_color_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process combination input from admin and save to file"""

    combination_text = update.message.text
    user_info = context.user_data['color_info']
    brand = user_info['brand']

    # Combination data structure
    combination_data = {
        "formula": combination_text,
        "created_at": datetime.now().isoformat(),
        "created_by": update.effective_user.id
    }

    try:
        # Load existing combinations
        if os.path.exists(ANSWERS):
            with open(ANSWERS, 'r', encoding='utf-8') as f:
                combinations = json.load(f)
        else:
            combinations = {}

        # Generate unique key
        if 'burn_type' in user_info:
            combo_key = f"{user_info['burn_type']}_{user_info['intensity']}_{brand}"
        else:
            combo_key = f"{user_info['undertone']}_{brand}"

        # Add/update combination
        combinations[combo_key] = combination_data

        # Save to file
        with open(ANSWERS, 'w', encoding='utf-8') as f:
            json.dump(combinations, f, ensure_ascii=False, indent=4)

        await update.message.reply_text(
            text=f"✅ ترکیب با موفقیت ذخیره شد\n\n{combination_text}",  # "Combination saved successfully"
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main")]
            ])
        )

    except Exception as e:
        print(f"Error saving combination: {e}")
        await update.message.reply_text("⚠️ خطا در ذخیره ترکیب")  # "Error saving combination"

    finally:
        # Clean up
        context.user_data.pop('answer_color', None)
        context.user_data.pop('color_info', None)


async def handle_back_navigation(query, context: ContextTypes.DEFAULT_TYPE):
    """Handles back button navigation"""
    await query.answer()
    target = query.data.split(':')[2]

    if target == "color_start":
        await start_color_selection(query, context)
    elif target == "burn_type":
        await handle_burn_type(query, context)
    elif target == "intensity":
        await handle_burn_intensity(query, context)
    elif target == "undertone":
        await handle_undertone(query, context)
    elif target == "brands":
        await handle_brand_selection(query, context)


async def color_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler for color selection callback queries"""
    query = update.callback_query
    data = query.data.split(':')

    if data[1] == 'has_burn':
        await handle_burn_type(query, context)
    elif data[1] == 'no_burn':
        await handle_undertone(query, context)
    elif data[1] in ['purple', 'brown', 'gray']:
        await handle_burn_intensity(query, context)
    elif data[1] == 'intensity':
        await handle_brand_selection(query, context)
    elif data[1] == 'undertone':
        await handle_brand_selection(query, context)
    elif data[1] == 'brand':
        await send_final_result(query, context)
    elif data[1] == 'back':
        await handle_back_navigation(query, context)
    elif data[1] == 'back_to_brands':
        await handle_brand_selection(query, context)
    elif data[1] == 'start':
        await start_color_selection(query, context)