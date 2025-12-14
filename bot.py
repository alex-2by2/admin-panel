import telebot
import os
import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_ADMINS = os.environ.get("BOT_ADMINS", "").split(",")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
db.init_db()


# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "🤖 Channel Auto Caption Bot is running")


# ---------- CHANNEL ENABLE CHECK ----------
def channel_enabled(channel_id):
    doc = db.captions.find_one({
        "type": "channel_status",
        "channel_id": str(channel_id)
    })
    return doc["enabled"] if doc else True


# ---------- INLINE BUTTON BUILDER ----------
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
    for row in data.get("rows", []):
        kb.row(*[
            InlineKeyboardButton(text=b["text"], url=b["url"])
            for b in row
        ])
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


# ---------- TEXT ----------
@bot.channel_post_handler(content_types=["text"])
def text_handler(m):
    if not channel_enabled(m.chat.id):
        return

    caption = get_caption("text_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=m.message_id,
        text=m.text + "\n\n" + caption,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


# ---------- PHOTO ----------
@bot.channel_post_handler(content_types=["photo"])
def photo_handler(m):
    if not channel_enabled(m.chat.id):
        return

    caption = get_caption("photo_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=caption,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


# ---------- VIDEO ----------
@bot.channel_post_handler(content_types=["video"])
def video_handler(m):
    if not channel_enabled(m.chat.id):
        return

    caption = get_caption("video_caption", m.chat.id)
    if not caption:
        return

    bot.edit_message_caption(
        chat_id=m.chat.id,
        message_id=m.message_id,
        caption=caption,
        reply_markup=get_inline_keyboard(m.chat.id)
    )


# ---------- BUTTON PREVIEW ----------
@bot.message_handler(commands=["preview_buttons"])
def preview_buttons(m):
    if str(m.from_user.id) not in BOT_ADMINS:
        return
    kb = get_inline_keyboard("default")
    bot.send_message(m.chat.id, "🔘 Button Preview", reply_markup=kb)


# ---------- BULK DELETE ----------
@bot.message_handler(commands=["clear_channel"])
def clear_channel(m):
    if str(m.from_user.id) not in BOT_ADMINS:
        return
    try:
        ch = m.text.split()[1]
        r = db.captions.delete_many({"channel_id": ch})
        bot.reply_to(m, f"✅ Deleted {r.deleted_count} records")
    except:
        bot.reply_to(m, "Usage: /clear_channel -100xxxx")


print("🤖 Bot running (FINAL)")
bot.infinity_polling()
