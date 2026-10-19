import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHOOSE_ACTION, GET_VILLAGE, GET_NAME, GET_SERVICE, GET_PHONE, SEARCH_VILLAGE = range(6)
DB_FILE = "database.json"

# Render Web Service үчүн жалган веб-сервер (бот өчүп калбаш үчүн)
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Jumush24 Bot Live")
    def log_message(self, *a): pass

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), H).serve_forever()

def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

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
    village = update.message.text
    context.user_data['search_village'] = village
    db = load_db()
    workers = db.get(village, [])
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 Көрүү - {len(workers)} жумушчу", callback_data="check_pay_search")]])
    await update.message.reply_text(f"{village} айылында {len(workers)} жумушчу бар.", reply_markup=kb)
    return CHOOSE_ACTION

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Айылыңызды жазыңыз:")
    return GET_VILLAGE

async def get_village(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['village'] = update.message.text
    await update.message.reply_text("Кызматыңызды жазыңыз:")
    return GET_SERVICE

async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['service'] = update.message.text
    village = context.user_data['village']
    db = load_db()
    if village not in db: db[village] = []
    db[village].append({'name': context.user_data['name'], 'service': context.user_data['service'], 'phone': 'Номер жок'})
    save_db(db)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Төлөдүм", callback_data="paid")]])
    await update.message.reply_text(f"✅ {village} базасына кошулдуңуз!", reply_markup=kb)
    return CHOOSE_ACTION

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(entry_points=[CommandHandler("start", start)], states={CHOOSE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action), CallbackQueryHandler(button)], GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)], GET_VILLAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_village)], GET_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)], SEARCH_VILLAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_village_search)]}, fallbacks=[CommandHandler("start", start)])
    app.add_handler(conv)
    print("Bot ishtep jatat...")
    app.run_polling()
