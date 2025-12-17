import telebot
import os
import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()

# ---------- CHANNEL ENABLE ----------
def is_channel_enabled(channel_id):
    doc = db.captions.find_one({
        "type": "channel_status",
        "channel_id": str(channel_id)
    })
    return doc.get("enabled", True) if doc else True


# ---------- HEADER ENABLE ----------
def is_header_enabled(channel_id):
    doc = db.captions.find_one({
        "type": "header_status",
        "channel_id": str(channel_id)
    })
    return doc.get("enabled", True) if doc else True


# ---------- HEADER TEXT ----------
def get_header(channel_id):
    doc = db.captions.find_one({
        "type": "header",
        "channel_id": str(channel_id)
    })
    if doc:
        return doc["text"]

    doc = db.captions.find_one({
        "type": "header",
        "channel_id": "default"
    })
    return doc["text"] if doc else None


# ---------- INLINE BUTTONS ----------
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
    for b in data.get("buttons", []):
        kb.add(InlineKeyboardButton(text=b["text"], url=b["url"]))
    return kb


# ---------- CAPTION ----------
def get_caption(caption_type, channel_id):
    doc = db.captions.find_one({
        "type": caption_type,
        "channel_id": str(channel_id)
    }) or db.captions.find_one({
        "type": caption_type,
        "channel_id": "default"
    })

    return doc["text"] if doc else None


@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "🤖 Channel Auto Caption Bot is running")


# ---------- TEXT ----------
@bot.channel_post_handler(content_types=["text"])
def text_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_caption("text_caption", m.chat.id)
    if not caption:
        return

    final = ""
    if is_header_enabled(m.chat.id):
        header = get_header(m.chat.id)
        if header:
            final += header + "\n\n"

    final += m.text + "\n\n" + caption

    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=m.message_id,
        text=final,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


# ---------- PHOTO ----------
@bot.channel_post_handler(content_types=["photo"])
def photo_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_caption("photo_caption", m.chat.id)
    if not caption:
        return

    final = ""
    if is_header_enabled(m.chat.id):
        header = get_header(m.chat.id)
        if header:
            final += header + "\n\n"

    final += caption

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=final,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


# ---------- VIDEO ----------
@bot.channel_post_handler(content_types=["video"])
def video_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_caption("video_caption", m.chat.id)
    if not caption:
        return

    final = ""
    if is_header_enabled(m.chat.id):
        header = get_header(m.chat.id)
        if header:
            final += header + "\n\n"

    final += caption

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=final,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


print("🤖 Bot running")
bot.infinity_polling()
