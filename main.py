import os, threading, sqlite3, logging, asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver
from groq import Groq

# --- 1. المحرك الحي (Keep Alive) لضمان استقرار Render ---
def run_keep_alive():
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"BAC 2026 Empire is Standing Strong!")
    
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()

# --- 2. الإعدادات والبيئة ---
TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
BAC_DATE = datetime(2026, 6, 15)

def init_db():
    conn = sqlite3.connect("bac_algeria.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, warns INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# --- 3. محرك البوت الذكي ---
class HamzaProBot:
    def __init__(self):
        init_db()
        # بناء التطبيق مع إعدادات منع التعارض
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        days_left = (BAC_DATE - datetime.now()).days
        
        # تخزين المستخدم
        conn = sqlite3.connect("bac_algeria.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.commit()
        conn.close()

        keyboard = [
            [InlineKeyboardButton("📚 ترسانة الدروس DZ", callback_data="edu"), InlineKeyboardButton("🧠 العقل الاصطناعي", callback_data="ai_call")],
            [InlineKeyboardButton("📊 بروفايلي الملكي", callback_data="me"), InlineKeyboardButton("🏆 قائمة النخبة", callback_data="top")],
            [InlineKeyboardButton("📅 عداد الحسم", callback_data="timer")]
        ]
        
        msg = (f"🏰 **أهلاً بك في عرين إمبراطورية البكالوريا {user.first_name}**\n\n"
               f"🇩🇿 **باك 2026:** نحن هنا لنصنع المجد!\n"
               f"⏳ **باقي على الحلم:** {days_left} يوم\n\n"
               "سيرفر الإمبراطور يعمل بأقصى طاقة 🚀")
        
        if update.message:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer() # استجابة فورية لمنع تعليق الزر

        if query.data == "me":
            conn = sqlite3.connect("bac_algeria.db")
            res = conn.execute("SELECT xp, warns FROM users WHERE id=?", (query.from_user.id,)).fetchone()
            xp, warns = (res[0], res[1]) if res else (0, 0)
            
            status = "🟢 منضبط" if warns == 0 else "🟡 تحت الرقابة" if warns < 3 else "🔴 خطر"
            msg = (f"👤 **ملفك الإمبراطوري:**\n\n"
                   f"⭐ **نقاط الخبرة:** `{xp} XP`\n"
                   f"⚠️ **الإنذارات:** `{warns}/3`\n"
                   f"🛡️ **الحالة:** {status}")
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")
        
        elif query.data == "top":
            conn = sqlite3.connect("bac_algeria.db")
            top = conn.execute("SELECT name, xp FROM users ORDER BY xp DESC LIMIT 5").fetchall()
            msg = "🏆 **نخبة الإمبراطورية (الأوائل):**\n\n"
            for i, u in enumerate(top):
                msg += f"{['🥇','🥈','🥉','🎖️','🎖️'][i]} {u[0]} — `{u[1]} XP`\n"
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

        elif query.data == "home":
            await self.start(update, context)

    async def admin_warn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # ميزة البطاقة الصفراء والحمراء
        if not update.message.reply_to_message:
            return await update.message.reply_text("❌ رد على رسالة الشخص لإعطائه بطاقة!")
        
        target = update.message.reply_to_message.from_user
        conn = sqlite3.connect("bac_algeria.db")
        conn.execute("UPDATE users SET warns = warns + 1 WHERE id = ?", (target.id,))
        warns = conn.execute("SELECT warns FROM users WHERE id = ?", (target.id,)).fetchone()[0]
        conn.commit()
        
        if warns >= 3:
            await update.message.reply_text(f"🔴 **بطاقة حمراء!** تم طرد {target.first_name} بسبب التشويش.")
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        else:
            await update.message.reply_text(f"🟡 **بطاقة صفراء!** {target.first_name}، إنذار رقم {warns}. التزم بالقوانين!")

    async def global_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text: return
        text = update.message.text
        user = update.effective_user

        # زيادة XP تلقائي
        conn = sqlite3.connect("bac_algeria.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.execute("UPDATE users SET xp = xp + 1 WHERE id = ?", (user.id,))
        conn.commit()

        # الذكاء الاصطناعي بلمسة جزائرية
        if text.startswith("سؤال"):
            prompt = text.replace("سؤال", "").strip()
            waiting = await update.message.reply_text("🌀 جاري استدعاء العقل الإمبراطوري...")
            try:
                client = Groq(api_key=GROQ_KEY)
                res = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"أنت مساعد طالب بكالوريا جزائري، أجب بوضوح وتشجيع: {prompt}"}],
                    model="llama3-70b-8192"
                )
                await waiting.edit_text(f"🤖 **إجابة العقل الذكي:**\n\n{res.choices[0].message.content}")
            except:
                await waiting.edit_text("❌ العقل مشغول حالياً، حاول لاحقاً!")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("warn", self.admin_warn))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.global_monitor))

    def run(self):
        threading.Thread(target=run_keep_alive, daemon=True).start()
        # أهم سطر لمنع الـ Conflict وتكرار البوت
        self.app.run_polling(drop_pending_updates=True, stop_signals=None)

if __name__ == "__main__":
    HamzaProBot().run()
