import telebot
import os
import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()

# ---------- CHANNEL ENABLE CHECK ----------
def is_channel_enabled(channel_id):
    doc = db.captions.find_one({
        "type": "channel_status",
        "channel_id": str(channel_id)
    })

    # If not found → enabled by default
    if not doc:
        return True

    return doc.get("enabled", True)

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Channel Auto Caption Bot is running")


# ---------- INLINE BUTTON (DEFAULT + CHANNEL) ----------
def get_inline_keyboard(channel_id):
    # 1️⃣ Channel specific
    data = db.captions.find_one({
        "type": "inline_buttons",
        "channel_id": str(channel_id)
    })

    # 2️⃣ Default fallback
    if not data:
        data = db.captions.find_one({
            "type": "inline_buttons",
            "channel_id": "default"
        })

    if not data:
        return None

    kb = InlineKeyboardMarkup()
    for b in data["buttons"]:
        kb.add(InlineKeyboardButton(text=b["text"], url=b["url"]))
    return kb


# ---------- CAPTION RESOLVER (IMPORTANT) ----------
def get_caption(caption_type, channel_id):
    # 1️⃣ Channel specific caption
    doc = db.captions.find_one({
        "type": caption_type,
        "channel_id": str(channel_id)
    })
    if doc:
        return doc["text"]

    # 2️⃣ Default caption
    doc = db.captions.find_one({
        "type": caption_type,
        "channel_id": "default"
    })
    if doc:
        return doc["text"]

    return None
# ---------- HEADER RESOLVER ----------
def get_header(channel_id):
    # 1️⃣ Channel specific header
    doc = db.captions.find_one({
        "type": "header",
        "channel_id": str(channel_id)
    })
    if doc:
        return doc["text"]

    # 2️⃣ Default header
    doc = db.captions.find_one({
        "type": "header",
        "channel_id": "default"
    })
    if doc:
        return doc["text"]

    return None

# ---------- TEXT POSTS ----------
@bot.channel_post_handler(content_types=["text"])
def handle_text(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_caption("text_caption", m.chat.id)
    header = get_header(m.chat.id)

    if not caption:
        return

    final_text = ""
    if header:
        final_text += header + "\n\n"

    final_text += m.text + "\n\n" + caption

    try:
        bot.edit_message_text(
            chat_id=m.chat.id,
            message_id=m.message_id,
            text=final_text,
            reply_markup=get_inline_keyboard(m.chat.id)
        )
    except Exception as e:
        print("Text error:", e)
# ---------- PHOTO POSTS ----------
@bot.channel_post_handler(content_types=["photo"])
def handle_photo(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_caption("photo_caption", m.chat.id)
    header = get_header(m.chat.id)

    if not caption:
        return

    final_caption = ""
    if header:
        final_caption += header + "\n\n"

    final_caption += caption

    try:
        bot.edit_message_caption(
            chat_id=m.chat.id,
            message_id=m.message_id,
            caption=final_caption,
            reply_markup=get_inline_keyboard(m.chat.id)
        )
    except Exception as e:
        print("Photo error:", e)
# ---------- VIDEO POSTS ----------
@bot.channel_post_handler(content_types=["video"])
def handle_video(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_caption("video_caption", m.chat.id)
    header = get_header(m.chat.id)

    if not caption:
        return

    final_caption = ""
    if header:
        final_caption += header + "\n\n"

    final_caption += caption

    try:
        bot.edit_message_caption(
            chat_id=m.chat.id,
            message_id=m.message_id,
            caption=final_caption,
            reply_markup=get_inline_keyboard(m.chat.id)
        )
    except Exception as e:
        print("Video error:", e)
print("🤖 Bot running with DEFAULT + CHANNEL captions")
bot.infinity_polling()
