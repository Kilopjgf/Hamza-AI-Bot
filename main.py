import os
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))

# ================== HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    text = update.message.text.lower()

    if "سؤال" in text:
        await update.message.reply_text("🧠 سؤال اليوم: ما هو مشتق الدالة x² ؟")

    elif "لغز" in text:
        await update.message.reply_text("🧩 لغز: شيء يمشي بلا قدمين ويبكي بلا عينين؟")

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
