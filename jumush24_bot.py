import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "TOKEN_JERGE_JAZ")
CHOOSE_ACTION, GET_VILLAGE, GET_NAME, GET_SERVICE, GET_PHONE, SEARCH_VILLAGE = range(6)
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([["📦 Иш табуу", "🧑‍🔧 Жумушчу болом"]], resize_keyboard=True)
    await update.message.reply_text("Салам! Jumush24 ботуна кош келиңиз!", reply_markup=kb)
    return CHOOSE_ACTION

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = load_db()
    if query.data == "check_pay_search":
        village = context.user_data.get('search_village')
        workers = db.get(village, [])
        if not workers:
            await query.message.reply_text(f"{village} айылында азырынча жумушчу жок.")
        else:
            text = f"📋 {village} боюнча:\n\n"
            for i, w in enumerate(workers, 1):
                text += f"{i}. {w['name']} - {w['service']} - {w['phone']}\n"
            await query.message.reply_text(text)
    else:
        await query.message.reply_text("✅ Төлөм кабыл алынды! Сиз базага кошулдуңуз.")
        return ConversationHandler.END

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Иш табуу" in text:
        await update.message.reply_text("Айылыңыздын атын жазыңыз:")
        return SEARCH_VILLAGE
    else:
        await update.message.reply_text("Атыңызды жазыңыз:")
        return GET_NAME

async def get_village_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    village = update.message
