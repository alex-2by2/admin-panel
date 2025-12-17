import telebot
import os
import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()

# ================= HELPERS =================

def is_channel_enabled(channel_id):
    doc = db.captions.find_one({
        "type": "channel_status",
        "channel_id": str(channel_id)
    })
    return doc.get("enabled", True) if doc else True


def get_status(name, channel_id):
    # Channel specific
    doc = db.captions.find_one({
        "type": name,
        "channel_id": str(channel_id)
    })
    if doc:
        return doc.get("enabled", True)

    # Default fallback
    doc = db.captions.find_one({
        "type": name,
        "channel_id": "default"
    })
    return doc.get("enabled", True) if doc else True


def get_text(name, channel_id):
    # Channel specific
    doc = db.captions.find_one({
        "type": name,
        "channel_id": str(channel_id)
    })
    if doc:
        return doc.get("text")

    # Default fallback
    doc = db.captions.find_one({
        "type": name,
        "channel_id": "default"
    })
    return doc.get("text") if doc else None


# ================= INLINE BUTTONS (ROW SUPPORT) =================
def get_buttons(channel_id):
    # Channel specific
    doc = db.captions.find_one({
        "type": "inline_buttons",
        "channel_id": str(channel_id)
    })

    # Default fallback
    if not doc:
        doc = db.captions.find_one({
            "type": "inline_buttons",
            "channel_id": "default"
        })

    if not doc or "buttons" not in doc:
        return None

    kb = InlineKeyboardMarkup()

    # buttons = [ [ {text,url}, {text,url} ], [ {text,url} ] ]
    for row in doc["buttons"]:
        btn_row = []
        for b in row:
            btn_row.append(
                InlineKeyboardButton(
                    text=b["text"],
                    url=b["url"]
                )
            )
        kb.row(*btn_row)

    return kb


# ================= TEXT POSTS =================
@bot.channel_post_handler(content_types=["text"])
def text_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_text("text_caption", m.chat.id)
    if not caption:
        return

    final = ""

    # HEADER
    if get_status("header_status", m.chat.id):
        header = get_text("header", m.chat.id)
        if header:
            final += header + "\n\n"

    final += m.text + "\n\n" + caption

    # FOOTER
    if get_status("footer_status", m.chat.id):
        footer = get_text("footer", m.chat.id)
        if footer:
            final += "\n\n" + footer

    try:
        bot.edit_message_text(
            chat_id=m.chat.id,
            message_id=m.message_id,
            text=final,
            reply_markup=get_buttons(m.chat.id)
        )
    except Exception as e:
        print("TEXT ERROR:", e)


# ================= PHOTO POSTS =================
@bot.channel_post_handler(content_types=["photo"])
def photo_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_text("photo_caption", m.chat.id)
    if not caption:
        return

    final = ""

    # HEADER
    if get_status("header_status", m.chat.id):
        header = get_text("header", m.chat.id)
        if header:
            final += header + "\n\n"

    final += caption

    # FOOTER
    if get_status("footer_status", m.chat.id):
        footer = get_text("footer", m.chat.id)
        if footer:
            final += "\n\n" + footer

    try:
        bot.edit_message_caption(
            chat_id=m.chat.id,
            message_id=m.message_id,
            caption=final,
            reply_markup=get_buttons(m.chat.id)
        )
    except Exception as e:
        print("PHOTO ERROR:", e)


# ================= VIDEO POSTS =================
@bot.channel_post_handler(content_types=["video"])
def video_post(m):
    if not is_channel_enabled(m.chat.id):
        return

    caption = get_text("video_caption", m.chat.id)
    if not caption:
        return

    final = ""

    # HEADER
    if get_status("header_status", m.chat.id):
        header = get_text("header", m.chat.id)
        if header:
            final += header + "\n\n"

    final += caption

    # FOOTER
    if get_status("footer_status", m.chat.id):
        footer = get_text("footer", m.chat.id)
        if footer:
            final += "\n\n" + footer

    try:
        bot.edit_message_caption(
            chat_id=m.chat.id,
            message_id=m.message_id,
            caption=final,
            reply_markup=get_buttons(m.chat.id)
        )
    except Exception as e:
        print("VIDEO ERROR:", e)


# ================= RUN =================
print("🤖 Bot running (Header + Footer + Multi-Row Buttons)")
bot.infinity_polling()
