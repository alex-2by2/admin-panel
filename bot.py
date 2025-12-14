import telebot
import os
import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
db.init_db()


# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Channel Auto Caption Bot is running")


# ---------- INLINE BUTTON ----------
def get_inline_keyboard():
    if db.captions is None:
        return None

    data = db.captions.find_one({"type": "inline_button"})
    if not data:
        return None

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text=data["text"], url=data["url"]))
    return kb


# ---------- TEXT POSTS ----------
@bot.channel_post_handler(content_types=['text'])
def handle_text(message):
    doc = db.captions.find_one({"type": "text_caption"})
    if not doc:
        return

    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=message.text + "\n\n" + doc["text"],
            reply_markup=get_inline_keyboard()
        )
    except Exception as e:
        print("Text error:", e)


# ---------- PHOTO POSTS ----------
@bot.channel_post_handler(content_types=['photo'])
def handle_photo(message):
    doc = db.captions.find_one({"type": "photo_caption"})
    if not doc:
        return

    try:
        bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.message_id,
            caption=doc["text"],
            reply_markup=get_inline_keyboard()
        )
    except Exception as e:
        print("Photo error:", e)


# ---------- VIDEO POSTS ----------
@bot.channel_post_handler(content_types=['video'])
def handle_video(message):
    doc = db.captions.find_one({"type": "video_caption"})
    if not doc:
        return

    try:
        bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.message_id,
            caption=doc["text"],
            reply_markup=get_inline_keyboard()
        )
    except Exception as e:
        print("Video error:", e)


print("🤖 Bot running with captions + inline buttons")
bot.infinity_polling()
