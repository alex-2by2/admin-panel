import telebot
import os
import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Channel Auto Caption Bot is running")


def get_inline_keyboard():
    data = db.captions.find_one({"type": "inline_buttons"})
    if not data:
        return None

    kb = InlineKeyboardMarkup()
    for b in data["buttons"]:
        kb.add(InlineKeyboardButton(text=b["text"], url=b["url"]))
    return kb


def get_caption(caption_type, channel_id):
    doc = db.captions.find_one({
        "type": caption_type,
        "channel_id": str(channel_id)
    })
    return doc["text"] if doc else None


@bot.channel_post_handler(content_types=["text"])
def text_handler(m):
    caption = get_caption("text_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=m.message_id,
        text=m.text + "\n\n" + caption,
        reply_markup=get_inline_keyboard()
    )


@bot.channel_post_handler(content_types=["photo"])
def photo_handler(m):
    caption = get_caption("photo_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=caption,
        reply_markup=get_inline_keyboard()
    )


@bot.channel_post_handler(content_types=["video"])
def video_handler(m):
    caption = get_caption("video_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=caption,
        reply_markup=get_inline_keyboard()
    )


print("🤖 Bot running with multi-channel captions + mobile admin UI")
bot.infinity_polling()
