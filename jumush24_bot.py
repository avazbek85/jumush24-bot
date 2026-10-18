import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💼 Жумушчу керек", callback_data='find_job')],
        [InlineKeyboardButton("📢 Жумуш берүү", callback_data='post_job')],
        [InlineKeyboardButton("📞 Байланыш", callback_data='contact')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Салам! Jumush24 ботуна кош келиңиз! 👋\nБул жерден жумуш таба аласыз!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'find_job':
        await query.edit_message_text("💼 Жумуштар:\n1. Официант - 1500с\n2. Курьер - 2000с\n\n@jumush24")
    elif query.data == 'post_job':
        await query.edit_message_text("📢 Жумуш берүү үчүн: @jumush24_admin")
    else:
        await query.edit_message_text("📞 Байланыш: @jumush24_admin")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
