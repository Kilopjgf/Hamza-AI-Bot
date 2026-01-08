import os, threading, sqlite3, logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver
from groq import Groq

# --- حل مشكلة البورت لـ Render ---
def run_keep_alive():
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"BAC Algeria Empire is Awake!")
    
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()

# --- إعدادات البيئة وقاعدة البيانات ---
TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
BAC_DATE = datetime(2026, 6, 15) # الموعد التقريبي لباك 2026

def init_db():
    conn = sqlite3.connect("bac_dz.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, warns INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

class BacEmpireBot:
    def __init__(self):
        init_db()
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        days_left = (BAC_DATE - datetime.now()).days
        
        keyboard = [
            [InlineKeyboardButton("📚 ترسانة الدروس (DZ)", callback_data="edu"), InlineKeyboardButton("🧠 سؤال جماعي AI", callback_data="ai")],
            [InlineKeyboardButton("🏆 قائمة النخبة", callback_data="top"), InlineKeyboardButton("👤 ملفي الملكي", callback_data="profile")],
            [InlineKeyboardButton("📅 عداد الحسم", callback_data="timer")]
        ]
        
        text = (f"🏰 **مرحباً بك في عرين إمبراطورية البكالوريا {user.first_name}**\n\n"
                f"🎯 **الهدف:** كرتونة 2026 بمعدل ممتاز 🎓\n"
                f"⏳ **متبقي للحسم:** {days_left} يوم\n\n"
                "اختر وجهتك القتالية 👇")
        
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        if query.data == "profile":
            conn = sqlite3.connect("bac_dz.db")
            res = conn.execute("SELECT xp, warns FROM users WHERE id=?", (user_id,)).fetchone()
            xp, warns = (res[0], res[1]) if res else (0, 0)
            conn.close()
            
            bar = "▰" * (xp // 100) + "▱" * (10 - (xp // 100)) # شريط تقدم بسيط
            msg = (f"👤 **بطاقة التعريف المدرسية:**\n\n"
                   f"⭐ **النقاط:** `{xp} XP`\n"
                   f"⚠️ **الإنذارات:** `{warns}/3`\n"
                   f"📊 **مستوى الجاهزية:**\n`{bar}`")
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")
        
        elif query.data == "top":
            conn = sqlite3.connect("bac_dz.db")
            top = conn.execute("SELECT name, xp FROM users ORDER BY xp DESC LIMIT 5").fetchall()
            conn.close()
            msg = "🏆 **نخبة الإمبراطورية (الأوائل):**\n\n"
            for i, u in enumerate(top): msg += f"{['🥇','🥈','🥉','🎖️','🎖️'][i]} {u[0]} — `{u[1]} XP`\n"
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

        elif query.data == "home":
            await self.start(update, context)

    # --- نظام العقوبات الملكي (أوامر الإدارة) ---
    async def admin_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            return await update.message.reply_text("❌ رد على رسالة 'المشاغب' لإعطائه البطاقة!")
        
        target = update.message.reply_to_message.from_user
        conn = sqlite3.connect("bac_dz.db")
        conn.execute("UPDATE users SET warns = warns + 1 WHERE id = ?", (target.id,))
        res = conn.execute("SELECT warns FROM users WHERE id = ?", (target.id,)).fetchone()
        conn.commit()
        conn.close()

        warn_count = res[0] if res else 1
        if warn_count >= 3:
            await update.message.reply_text(f"🔴 **بطاقة حمراء!** تم طرد {target.first_name} بسبب كثرة التشويش.")
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        else:
            await update.message.reply_text(f"🟡 **بطاقة صفراء!** {target.first_name}، هذا الإنذار رقم {warn_count}. التزم بالدراسة!")

    async def chat_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text: return
        text = update.message.text
        user = update.effective_user

        # زيادة نقاط التفاعل في القروب تلقائياً
        conn = sqlite3.connect("bac_dz.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.execute("UPDATE users SET xp = xp + 1 WHERE id = ?", (user.id,))
        conn.commit()
        conn.close()

        if text.startswith("سؤال"):
            prompt = text.replace("سؤال", "").strip()
            msg = await update.message.reply_text("🌀 جاري استدعاء العقل الإمبراطوري...")
            client = Groq(api_key=GROQ_KEY)
            res = client.chat.completions.create(messages=[{"role": "user", "content": f"أجب بلهجة جزائرية تشجيعية لطلاب البكالوريا: {prompt}"}], model="llama3-70b-8192")
            await msg.edit_text(f"🤖 **الإجابة:**\n\n{res.choices[0].message.content}")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("warn", self.admin_warn)) # أمر البطاقة
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat_monitor))

    def run(self):
        threading.Thread(target=run_keep_alive, daemon=True).start()
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    BacEmpireBot().run()
