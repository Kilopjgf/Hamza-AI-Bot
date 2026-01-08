import os, sqlite3, json, random, threading, logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import http.server
import socketserver

# ==================== نظام خدع Render (المنفذ الوهمي) ====================
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🛰️ المنفذ الملكي يعمل على البورت: {port}")
        httpd.serve_forever()

# ==================== الإعدادات الأساسية ====================
TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BAC_DATE = datetime(2026, 6, 15)

# ==================== قاعدة البيانات المركزية ====================
def init_db():
    conn = sqlite3.connect("study_empire.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, rank TEXT DEFAULT 'محارب')''')
    conn.commit()
    conn.close()

# ==================== محرك الإمبراطورية ====================
class HamzaEmpire:
    def __init__(self):
        init_db()
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    def _get_rank(self, points):
        if points > 5000: return "👑 الإمبراطور"
        if points > 2000: return "🎖️ الجنرال"
        if points > 500: return "⚔️ القائد"
        return "🛡️ محارب"

    def _get_progress_bar(self):
        total_days = 270 # معدل أيام السنة الدراسية
        remaining = (BAC_DATE - datetime.now()).days
        passed = total_days - remaining
        filled = int((passed / total_days) * 10)
        return "▬" * filled + "▷" + "▭" * (10 - filled)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        bar = self._get_progress_bar()
        remaining = (BAC_DATE - datetime.now()).days
        
        # تخزين المستخدم في القاعدة
        conn = sqlite3.connect("study_empire.db")
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.commit()
        conn.close()

        keyboard = [
            [InlineKeyboardButton("📚 ترسانة الدروس", callback_data="lessons"), InlineKeyboardButton("🧠 ذكاء Groq", callback_data="ai_chat")],
            [InlineKeyboardButton("🏆 ترتيب العمالقة", callback_data="top"), InlineKeyboardButton("👤 بروفايلي الملكي", callback_data="profile")],
            [InlineKeyboardButton("⏰ عداد الحسم", callback_data="timer")]
        ]

        msg = (f"👋 **أهلاً بك في عرين الإمبراطورية!**\n\n"
               f"👤 **المجاهد:** {user.first_name}\n"
               f"⏳ **الحسم:** {remaining} يوم\n"
               f"📊 **التقدم:** `{bar}`\n\n"
               f"⚡ _أنت هنا لتصنع مجدك، فابدأ الهجوم الآن!_")
        
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        if query.data == "profile":
            conn = sqlite3.connect("study_empire.db")
            c = conn.cursor()
            c.execute("SELECT points, level FROM users WHERE user_id=?", (user_id,))
            res = c.fetchone()
            pts = res[0] if res else 0
            rank = self._get_rank(pts)
            
            text = (f"⚜️ **بطاقة الهوية الإمبراطورية** ⚜️\n\n"
                    f"🎖️ **الرتبة:** {rank}\n"
                    f"⭐ **النقاط:** {pts} XP\n"
                    f"📖 **المستوى:** {res[1] if res else 1}\n\n"
                    f"🔥 _استمر في الدراسة لترقية رتبتك!_")
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="back")]]), parse_mode="Markdown")
        
        elif query.data == "back":
            # إعادة استدعاء قائمة البداية (تعديل الرسالة)
            await self.start(update, context)

    async def auto_guard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # نظام حماية القروب من الروابط الغريبة
        if update.message and update.message.text:
            if "http" in update.message.text.lower() and not update.message.from_user.id == 8518151371: # ضع آيديك هنا للاستثناء
                await update.message.delete()
                await update.message.reply_text(f"🚫 **ممنوع الروابط!**\nهنا ندرس فقط يا {update.effective_user.first_name}")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.handle_buttons))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.auto_guard))

    def run(self):
        # تشغيل السيرفر الوهمي في خيط منفصل لـ Render
        threading.Thread(target=run_dummy_server, daemon=True).start()
        print("🚀 الإمبراطورية جاهزة للغزو...")
        self.app.run_polling()

if __name__ == "__main__":
    HamzaEmpire().run()
