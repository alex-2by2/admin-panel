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


# ---------- INLINE KEYBOARD ----------
def get_inline_keyboard(channel_id):
    data = db.captions.find_one({
        "type": "inline_buttons",
        "channel_id": str(channel_id)
    }) or db.captions.find_one({
        "type": "inline_buttons",
        "channel_id": "default"
    })

    if not data:
        return None

    kb = InlineKeyboardMarkup()

    # NEW FORMAT (rows)
    rows = data.get("rows", [])
    for row in rows:
        buttons = []
        for b in row:
            buttons.append(
                InlineKeyboardButton(text=b["text"], url=b["url"])
            )
        kb.row(*buttons)

    return kb


# ---------- CAPTION RESOLVER ----------
def get_caption(caption_type, channel_id):
    doc = db.captions.find_one({
        "type": caption_type,
        "channel_id": str(channel_id)
    }) or db.captions.find_one({
        "type": caption_type,
        "channel_id": "default"
    })

    return doc["text"] if doc else None


@bot.channel_post_handler(content_types=["text"])
def handle_text(m):
    caption = get_caption("text_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=m.message_id,
        text=m.text + "\n\n" + caption,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


@bot.channel_post_handler(content_types=["photo"])
def handle_photo(m):
    caption = get_caption("photo_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=caption,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


@bot.channel_post_handler(content_types=["video"])
def handle_video(m):
    caption = get_caption("video_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=caption,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


print("🤖 Bot running with ROW-BASED inline buttons")
bot.infinity_polling()
