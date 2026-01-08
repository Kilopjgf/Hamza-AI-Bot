import os, threading, sqlite3, logging, asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver
from groq import Groq

# --- 1. نظام القلب النابض (تجاوز توقف Render) ---
def run_keep_alive():
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"BAC 2026 ELITE SYSTEM IS ACTIVE")
    
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()

# --- 2. إعدادات الإمبراطورية ---
TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
BAC_DATE = datetime(2026, 6, 15)

def init_db():
    conn = sqlite3.connect("bac_elite.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, warns INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# --- 3. المحرك الإبداعي الجديد ---
class HamzaEliteBot:
    def __init__(self):
        init_db()
        # إضافة إعدادات حماية لمنع الـ Conflict
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        days_left = (BAC_DATE - datetime.now()).days
        
        # حفظ بيانات المستخدم لضمان عمل الأزرار
        conn = sqlite3.connect("bac_elite.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.commit()
        conn.close()

        keyboard = [
            [InlineKeyboardButton("📚 خزانة الدروس (DZ)", callback_data="edu"), InlineKeyboardButton("🧠 مستشار النخبة AI", callback_data="ai_help")],
            [InlineKeyboardButton("🎖️ بطاقتي الجامعية", callback_data="me"), InlineKeyboardButton("🔥 صراع العمالقة", callback_data="top")],
            [InlineKeyboardButton("📢 قناة التفوق", url="https://t.me/your_channel"), InlineKeyboardButton("⏳ موعد الحسم", callback_data="timer")]
        ]
        
        msg = (f"🏰 **أهلاً بك في نظام النخبة للبكالوريا {user.first_name}**\n\n"
               f"🇩🇿 **باك 2026:** طريقك نحو الـ 18/20 يبدأ هنا!\n"
               f"⏳ **متبقي:** {days_left} يوم من الصمود\n\n"
               f"✨ **الحالة:** السيرفر يعمل بأقصى سرعة تربو 🚀")
        
        if update.message:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        if query.data == "me":
            conn = sqlite3.connect("bac_elite.db")
            res = conn.execute("SELECT xp, warns FROM users WHERE id=?", (user_id,)).fetchone()
            xp, warns = (res
