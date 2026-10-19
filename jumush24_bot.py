import os, json, base64, requests, uuid
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
XPAY_ACCOUNT_ID = os.getenv("XPAY_ACCOUNT_ID", "e51e7cd9-c46e-4f37-966d-5d3cb9b8c160")
XPAY_CLIENT_ID = os.getenv("XPAY_CLIENT_ID")
XPAY_CLIENT_SECRET = os.getenv("XPAY_CLIENT_SECRET")

VILLAGES = ["Ак-Турпак","Жаңы-Жер","Жаш-Тилек","Жетиген","Калача","Кара-Тумшук","Келечек","Кызыл-Коргон","Мин-Чынар","Өрүкзар","Өтүкчү","Сары-Камыш","Токой","Чогорок","Чоң-Кара"]
VILLAGE_KB = [[v for v in VILLAGES[i:i+3]] for i in range(0, len(VILLAGES), 3)]
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE,'r',encoding='utf-8') as f: return json.load(f)
def save_db(d):
    with open(DB_FILE,'w',encoding='utf-8') as f: json.dump(f,d,ensure_ascii=False,indent=2)

def create_xpay_payment(amount_som, user_id, purpose):
    try:
        if not XPAY_CLIENT_ID or not XPAY_CLIENT_SECRET: return None
        url = "https://api.xpay.app/v1/checkout-sessions"
        auth = base64.b64encode(f"{XPAY_CLIENT_ID}:{XPAY_CLIENT_SECRET}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}","Content-Type":"application/json","X-Idempotency-Key": str(uuid.uuid4())}
        payload = {"account_id": XPAY_ACCOUNT_ID,"amount": int(amount_som*100),"currency":"KGS","external_id": f"{user_id}{purpose}{uuid.uuid4().hex[:6]}","description": f"Jumush24 - {purpose} - 20 KGS","success_url":"https://t.me/Jumush24_bot?start=paid"}
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        data = r.json()
        return data.get('url') or data.get('checkout_url') or data.get('payment_url')
    except Exception as e:
        print("XPay error:", e)
        return None 
CHOOSE_ACTION, CHOOSE_VILLAGE_REG, GET_NAME, GET_PHONE, GET_SERVICE, CHOOSE_VILLAGE_SEARCH, PAYMENT = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["💼 Иштеймин"],["🔍 Жумушчу издөө"]]
    await update.message.reply_text("Салам! Jumush24 👋\nТандаңыз:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CHOOSE_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "Иштеймин" in update.message.text:
        context.user_data['mode']='reg'
        await update.message.reply_text("Айылды тандаңыз:", reply_markup=ReplyKeyboardMarkup(VILLAGE_KB, resize_keyboard=True))
        return CHOOSE_VILLAGE_REG
    else:
        context.user_data['mode']='search'
        await update.message.reply_text("Кайсы айылдан издейсиз?", reply_markup=ReplyKeyboardMarkup(VILLAGE_KB, resize_keyboard=True))
        return CHOOSE_VILLAGE_SEARCH

async def get_village_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['village']=update.message.text
    await update.message.reply_text("Атыңызды жазыңыз:")
    return GET_NAME
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name']=update.message.text
    await update.message.reply_text("Тел номериңиз:")
    return GET_PHONE
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone']=update.message.text
    await update.message.reply_text("Кызматыңыз жана акысы? (Мисалы: Сантехник - 1000с)")
    return GET_SERVICE
    async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['service']=update.message.text
        village=context.user_data['village']
        db=load_db()
        if village not in db: db[village]=[]
        db[village].append({"name":context.user_data['name'],"phone":context.user_data['phone'],"service":context.user_data['service'],"paid":True})
        save_db(db)
        xpay_link=create_xpay_payment(20,update.effective_user.id,"registration") or "https://xpay.kg"
        kb=InlineKeyboardMarkup([[InlineKeyboardButton("💳 20 сом төлөө - XPay", url=xpay_link)],[InlineKeyboardButton("✅ Төлөдүм", callback_data="check_pay_reg")]])
        await update.message.reply_text(f"Айыл: {village}\nБазага кириш үчүн 20 сом төлөңүз:", reply_markup=kb)
        return PAYMENT

async def get_village_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    village=update.message.text
    context.user_data['search_village']=village
    db=load_db()
    count=len(db.get(village,[]))
    xpay_link=create_xpay_payment(20,update.effective_user.id,f"search_{village}") or "https://xpay.kg"
    kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"💳 20 сом төлөө - {count} жумушчу", url=xpay_link)],[InlineKeyboardButton("✅ Төлөдүм, номерлерди ал", callback_data="check_pay_search")]])
    await update.message.reply_text(f"{village} айылында {count} жумушчу бар. Номер алуу үчүн 20 сом:", reply_markup=kb)
    return PAYMENT

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query
    await query.answer()
    db=load_db()
    if query.data=="check_pay_search":
        village=context.user_data.get('search_village')
        workers=db.get(village,[])
        if not workers:
            await query.message.reply_text(f"{village} айылында азырынча жумушчу жок.")
        else:
            text=f"📋 {village} боюнча:\n\n"
            for i,w in enumerate(workers,1):
                text+=f"{i}. {w['name']} - {w['service']} - {w['phone']}\n"
            await query.message.reply_text(text)
    else:
        await query.message.reply_text("✅ Төлөм кабыл алынды! Сиз базага кошулдуңуз.")
    await query.message.reply_text("Башкы меню:", reply_markup=ReplyKeyboardMarkup([["💼 Иштеймин"],["🔍 Жумушчу издөө"]], resize_keyboard=True))
    return ConversationHandler.END

if _name=="main_":
    app=Application.builder().token(BOT_TOKEN).build()
    conv=ConversationHandler(entry_points=[CommandHandler("start", start)],states={CHOOSE_ACTION:[MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],CHOOSE_VILLAGE_REG:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_village_reg)],GET_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],GET_PHONE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],GET_SERVICE:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],CHOOSE_VILLAGE_SEARCH:[MessageHandler(filters.TEXT & ~filters.COMMAND, get_village_search)],PAYMENT:[CallbackQueryHandler(check_payment)]},fallbacks=[CommandHandler("start", start)])
    app.add_handler(conv)
    print("Бот иштеп жатат...")
    app.run_polling()
