import telebot, os, db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN=os.environ.get("BOT_TOKEN")
ADMIN_IDS=os.environ.get("BOT_ADMINS","").split(",")

bot=telebot.TeleBot(BOT_TOKEN,threaded=False)
db.init_db()

def get_buttons(cid):
    d=db.captions.find_one({"type":"inline_buttons","channel_id":str(cid)}) or \
      db.captions.find_one({"type":"inline_buttons","channel_id":"default"})
    if not d: return None
    kb=InlineKeyboardMarkup()
    for r in d["buttons"]:
        kb.row(*[InlineKeyboardButton(text=b["text"],url=b["url"]) for b in r])
    return kb

def get_caption(t,cid):
    d=db.captions.find_one({"type":t,"channel_id":str(cid)}) or \
      db.captions.find_one({"type":t,"channel_id":"default"})
    return d["text"] if d else None

@bot.channel_post_handler(content_types=["text","photo","video"])
def handle(m):
    t="text_caption" if m.content_type=="text" else f"{m.content_type}_caption"
    cap=get_caption(t,m.chat.id)
    if not cap: return
    if m.content_type=="text":
        bot.edit_message_text(m.text+"\n\n"+cap,m.chat.id,m.message_id,reply_markup=get_buttons(m.chat.id))
    else:
        bot.edit_message_caption(m.chat.id,m.message_id,cap,reply_markup=get_buttons(m.chat.id))

@bot.message_handler(commands=["delete_channel"])
def delete_channel(m):
    if str(m.from_user.id) not in ADMIN_IDS: return
    _,cid=m.text.split()
    r=db.captions.delete_many({"channel_id":cid})
    bot.reply_to(m,f"Deleted {r.deleted_count} items")

print("🤖 Bot running – FULL FEATURE SET")
bot.infinity_polling()
