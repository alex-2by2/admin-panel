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
@bot.channel_post_handler(func=lambda m: True)
def auto_caption_channel_post(message):
    if db.captions is None:
        return

    caption = None

    if message.photo:
        doc = db.captions.find_one({"type": "photo_caption"})
        caption = doc["text"] if doc else None

    elif message.video:
        doc = db.captions.find_one({"type": "video_caption"})
        caption = doc["text"] if doc else None

    elif message.text:
        doc = db.captions.find_one({"type": "text_caption"})
        caption = doc["text"] if doc else None
        if caption:
            caption = message.text + "\n\n" + caption

    if not caption:
        return

    try:
        if message.caption or message.photo or message.video:
            bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message.message_id,
                caption=caption
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=caption
            )
    except Exception as e:
        print("Edit failed:", e)
print("🤖 Bot running with channel auto-caption")

bot.infinity_polling(skip_pending=True)
