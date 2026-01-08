import os, threading, sqlite3, random, asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver

# --- 1. نظام القلب النابض (Keep Alive) ---
def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

# --- 2. الإعدادات والمعطيات ---
TOKEN = os.getenv("BOT_TOKEN")
BAC_DATE = datetime(2026, 6, 15)

# قاعدة البيانات المخففة لضمان السرعة
def init_db():
    conn = sqlite3.connect("hamza_empire.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# محتوى تحفيزي (آيات ونصائح)
MOTIVATION = [
    "✨ { وَأَن لَّيْسَ لِلْإِنسَانِ إِلَّا مَا سَعَىٰ } - شد الهمة يا بطل!",
    "💡 { إِنَّا لَا نُضِيعُ أَجْرَ مَنْ أَحْسَنَ عَمَلًا } - تعبك ماراحش يروح باطل.",
    "🚀 نصيحة: ابدأ بالمواد الصعبة في الصباح الباكر، عقلك يكون في قمة التركيز.",
    "📚 البكالوريا مجرد محطة، اجعلها محطة فخر لوالديك.",
    "✨ { فَإِذَا عَزَمْتَ فَتَوَكَّلْ عَلَى اللَّهِ } - ربي يوفقك يا وحش الباك."
]

class HamzaGoldenBot:
    def __init__(self):
        init_db()
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        days_left = (BAC_DATE - datetime.now()).days
        
        # واجهة الأزرار الجميلة
        keyboard = [
            [InlineKeyboardButton("⏳ عداد الحسم 2026", callback_data="timer")],
            [InlineKeyboardButton("📊 مستوى نشاطي", callback_data="status"), InlineKeyboardButton("🏆 العمالقة", callback_data="top")],
            [InlineKeyboardButton("✨ جرعة تفاؤل", callback_data="inspire")]
        ]
        
        welcome_text = (
            f"🏰 **مرحباً بك في عرين الإمبراطور {user.first_name}**\n\n"
            f"📖 **قال تعالى:** {{ وَاصْبِرْ لِحُكْمِ رَبِّكَ فَإِنَّكَ بِأَعْيُنِنَا }}\n\n"
            f"🎯 **هدفنا:** بكالوريا 2026 بمعدل يليق بك.\n"
            f"📈 **حالتك:** مسجل في قائمة النخبة ✅"
        )
        
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        if query.data == "timer":
            days = (BAC_DATE - datetime.now()).days
            msg = f"⏳ **العد التنازلي للبكالوريا:**\n\nباقي **{days}** يوم من الكفاح.\n\nاستغل كل دقيقة، الحلم يستحق!"
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

        elif query.data == "status":
            conn = sqlite3.connect("hamza_empire.db")
            res = conn.execute("SELECT xp FROM users WHERE id=?", (user_id,)).fetchone()
            xp = res[0] if res else 0
            
            rank = "🛡️ مبتدئ" if xp < 50 else "⚔️ مقاتل" if xp < 200 else "👑 إمبراطور"
            bar = "▰" * (min(xp // 20, 10)) + "▱" * (10 - min(xp // 20, 10))
            
            msg = (f"📊 **تحليل النشاط الخاص بك:**\n\n"
                   f"🎖️ **الرتبة:** {rank}\n"
                   f"🔥 **قوة التفاعل:** `{xp} XP`\n"
                   f"📈 **التقدم:**\n`{bar}`")
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

        elif query.data == "inspire":
            quote = random.choice(MOTIVATION)
            await query.edit_message_text(f"🌟 **رسالة من الإمبراطور لك:**\n\n{quote}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 رسالة أخرى", callback_data="inspire"), InlineKeyboardButton("🔙", callback_data="home")]]), parse_mode="Markdown")

        elif query.data == "top":
            conn = sqlite3.connect("hamza_empire.db")
            top = conn.execute("SELECT name, xp FROM users ORDER BY xp DESC LIMIT 5").fetchall()
            msg = "🏆 **قائمة نخبة المجموعة:**\n\n"
            for i, u in enumerate(top):
                msg += f"{['🥇','🥈','🥉','✨','✨'][i]} {u[0]} — `{u[1]} XP`\n"
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

        elif query.data == "home":
            await self.start(update, context)

    async def message_monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text: return
        user = update.effective_user

        # تسجيل النقاط لزيادة النشاط
        conn = sqlite3.connect("hamza_empire.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.execute("UPDATE users SET xp = xp + 1 WHERE id = ?", (user.id,))
        conn.commit()
        conn.close()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_monitor))

    def run(self):
        threading.Thread(target=run_keep_alive, daemon=True).start()
        # منع التعارض Conflict وتنظيف الطلبات القديمة
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    HamzaGoldenBot().run()
