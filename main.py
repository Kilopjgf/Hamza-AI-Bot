import os, threading, sqlite3, logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver
from groq import Groq

# --- 1. حل مشكلة البورت لـ Render ---
def run_keep_alive():
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Empire is Standing Strong!")
    
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()

# --- 2. الإعدادات وقاعدة البيانات ---
TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

def init_db():
    conn = sqlite3.connect("empire_final.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, warns INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# --- 3. المحرك الرئيسي ---
class HamzaMegaBot:
    def __init__(self):
        init_db()
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        keyboard = [
            [InlineKeyboardButton("🧠 سؤال جماعي (AI)", callback_data="ai_zone"), InlineKeyboardButton("📊 ملفي الإمبراطوري", callback_data="status")],
            [InlineKeyboardButton("🛡️ نظام العقوبات", callback_data="rules"), InlineKeyboardButton("🏆 العمالقة", callback_data="top")],
            [InlineKeyboardButton("📚 الترسانة", callback_data="edu")]
        ]
        welcome_msg = f"🏰 **أهلاً بك في عرين الإمبراطور {user.first_name}**\n\nنظام الإدارة والتعليم الذكي جاهز لخدمتك!"
        await (update.message.reply_text(welcome_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown") if update.message else update.callback_query.edit_message_text(welcome_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"))

    async def handle_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        if query.data == "status":
            conn = sqlite3.connect("empire_final.db")
            res = conn.execute("SELECT xp, warns FROM users WHERE id=?", (user_id,)).fetchone()
            xp = res[0] if res else 0
            warns = res[1] if res else 0
            msg = f"👤 **بروفايلك الملكي:**\n\n⭐ النقاط: `{xp} XP`\n⚠️ الإنذارات: `{warns}/3`"
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]))

        elif query.data == "rules":
            msg = "⚠️ **قوانين العرين:**\n1. يمنع السبام (بطاقة صفراء)\n2. يمنع الروابط (بطاقة حمراء)\n3. الاحترام واجب للجميع."
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]))

        elif query.data == "home":
            await self.start(update, context)

    # --- نظام العقوبات (أوامر للمشرفين) ---
    async def admin_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يجب الرد على رسالة المشاغب لإعطائه بطاقة!")
            return
        
        target_id = update.message.reply_to_message.from_user.id
        conn = sqlite3.connect("empire_final.db")
        conn.execute("UPDATE users SET warns = warns + 1 WHERE id = ?", (target_id,))
        res = conn.execute("SELECT warns FROM users WHERE id = ?", (target_id,)).fetchone()
        conn.commit()
        conn.close()

        warn_count = res[0] if res else 1
        if warn_count >= 3:
            await update.message.reply_text(f"🔴 **بطاقة حمراء!** تم طرد المستخدم لتجاوزه 3 إنذارات.")
            await context.bot.ban_chat_member(update.effective_chat.id, target_id)
        else:
            await update.message.reply_text(f"🟡 **بطاقة صفراء!** هذا هو الإنذار رقم {warn_count} لك.")

    # --- ذكاء اصطناعي سريع ---
    async def chat_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text: return
        text = update.message.text

        # زيادة نقاط التفاعل تلقائياً
        conn = sqlite3.connect("empire_final.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (update.effective_user.id, update.effective_user.first_name))
        conn.execute("UPDATE users SET xp = xp + 1 WHERE id = ?", (update.effective_user.id,))
        conn.commit()
        conn.close()

        if text.startswith("سؤال"):
            prompt = text.replace("سؤال", "").strip()
            msg = await update.message.reply_text("🌀 جاري استدعاء العقل...")
            client = Groq(api_key=GROQ_KEY)
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama3-70b-8192")
            await msg.edit_text(f"🤖 **الإجابة:**\n\n{res.choices[0].message.content}")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("warn", self.admin_warn)) # أمر البطاقة الصفراء/الحمراء
        self.app.add_handler(CallbackQueryHandler(self.handle_callbacks))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat_monitor))

    def run(self):
        threading.Thread(target=run_keep_alive, daemon=True).start()
        print("🚀 النسخة الملحمية قيد التشغيل...")
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    HamzaMegaBot().run()
