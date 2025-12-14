import telebot
import os
import db

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

db.init_db()

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "🤖 Channel Auto Caption Bot is running")

# ---------- CHANNEL POST HANDLER ----------
# ---------------- TEXT POSTS ----------------
@bot.channel_post_handler(content_types=['text'])
def handle_text_channel_post(message):
    if db.captions is None:
        return

    doc = db.captions.find_one({"type": "text_caption"})
    if not doc:
        return

    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=message.text + "\n\n" + doc["text"]
        )
    except Exception as e:
        print("Text edit failed:", e)


# ---------------- PHOTO POSTS ----------------
@bot.channel_post_handler(content_types=['photo'])
def handle_photo_channel_post(message):
    if db.captions is None:
        return

    doc = db.captions.find_one({"type": "photo_caption"})
    if not doc:
        return

    try:
        bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.message_id,
            caption=doc["text"]
        )
    except Exception as e:
        print("Photo edit failed:", e)


# ---------------- VIDEO POSTS ----------------
@bot.channel_post_handler(content_types=['video'])
def handle_video_channel_post(message):
    if db.captions is None:
        return

    doc = db.captions.find_one({"type": "video_caption"})
    if not doc:
        return

    try:
        bot.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.message_id,
            caption=doc["text"]
        )
    except Exception as e:
        print("Video edit failed:", e)
print("🤖 Bot running with channel auto-caption")

bot.infinity_polling(skip_pending=True)
