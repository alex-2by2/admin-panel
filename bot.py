import telebot
import os
import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()

# ---------- HELPERS ----------
def is_channel_enabled(channel_id):
    d = db.captions.find_one({"type": "channel_status", "channel_id": str(channel_id)})
    return d["enabled"] if d else True


def get_status(name, channel_id):
    d = db.captions.find_one({"type": name, "channel_id": str(channel_id)})
    if d:
        return d.get("enabled", True)

    d = db.captions.find_one({"type": name, "channel_id": "default"})
    return d.get("enabled", True) if d else True


def get_text(name, channel_id):
    d = db.captions.find_one({"type": name, "channel_id": str(channel_id)})
    if d:
        return d["text"]

    d = db.captions.find_one({"type": name, "channel_id": "default"})
    return d["text"] if d else None


def get_buttons(channel_id):
    d = db.captions.find_one({"type": "inline_buttons", "channel_id": str(channel_id)})
    if not d:
        d = db.captions.find_one({"type": "inline_buttons", "channel_id": "default"})
    if not d:
        return None

    kb = InlineKeyboardMarkup()
    for b in d["buttons"]:
        kb.add(InlineKeyboardButton(b["text"], url=b["url"]))
    return kb


# ---------- TEXT ----------
@bot.channel_post_handler(content_types=["text"])
def text_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_text("text_caption", m.chat.id)
    if not caption:
        return

    final = ""

    if get_status("header_status", m.chat.id):
        h = get_text("header", m.chat.id)
        if h:
            final += h + "\n\n"

    final += m.text + "\n\n" + caption

    if get_status("footer_status", m.chat.id):
        f = get_text("footer", m.chat.id)
        if f:
            final += "\n\n" + f

    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=m.message_id,
        text=final,
        reply_markup=get_buttons(m.chat.id)
    )


# ---------- PHOTO ----------
@bot.channel_post_handler(content_types=["photo"])
def photo_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_text("photo_caption", m.chat.id)
    if not caption:
        return

    final = ""

    if get_status("header_status", m.chat.id):
        h = get_text("header", m.chat.id)
        if h:
            final += h + "\n\n"

    final += caption

    if get_status("footer_status", m.chat.id):
        f = get_text("footer", m.chat.id)
        if f:
            final += "\n\n" + f

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=final,
        reply_markup=get_buttons(m.chat.id)
    )


# ---------- VIDEO ----------
@bot.channel_post_handler(content_types=["video"])
def video_post(m):
    photo_post(m)  # SAME LOGIC


print("🤖 Bot running with Header + Footer")
bot.infinity_polling()
