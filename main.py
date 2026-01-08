import os, threading, sqlite3, random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver

# --- 1. نظام النبض لضمان استقرار Render ---
def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

# --- 2. الإعدادات والمعطيات ---
TOKEN = os.getenv("BOT_TOKEN")
BAC_DATE = datetime(2026, 6, 15)

def init_db():
    conn = sqlite3.connect("hamza_pro_v2.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

MOTIVATION = [
    "✨ { وَأَن لَّيْسَ لِلْإِنسَانِ إِلَّا مَا سَعَىٰ } - شد الهمة يا بطل!",
    "💡 { إِنَّا لَا نُضِيعُ أَجْرَ مَنْ أَحْسَنَ عَمَلًا } - تعبك ماراحش يروح باطل.",
    "🚀 نصيحة: ابدأ بالمواد الصعبة في الصباح الباكر، عقلك يكون في قمة التركيز.",
    "✨ { فَإِذَا عَزَمْتَ فَتَوَكَّلْ عَلَى اللَّهِ } - ربي يوفقك يا وحش الباك."
]

class UltimateHamzaBot:
    def __init__(self):
        init_db()
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    # --- وظائف الرد الموحدة ---
    def get_timer(self):
        days = (BAC_DATE - datetime.now()).days
        return f"⏳ **العد التنازلي للبكالوريا 2026:**\n\nباقي **{days}** يوم على الحلم! استغل كل لحظة، فالمجد يُصنع الآن. 🇩🇿"

    def get_status(self, user_id, name):
        conn = sqlite3.connect("hamza_pro_v2.db")
        res = conn.execute("SELECT xp FROM users WHERE id=?", (user_id,)).fetchone()
        xp = res[0] if res else 0
        conn.close()
        rank = "🛡️ مبتدئ" if xp < 50 else "⚔️ مقاتل" if xp < 200 else "👑 إمبراطور"
        bar = "▰" * (min(xp // 20, 10)) + "▱" * (10 - min(xp // 20, 10))
        return f"📊 **ملفك الإمبراطوري يا {name}:**\n\n🎖️ الرتبة: {rank}\n🔥 النقاط: `{xp} XP`\n📈 النشاط: `{bar}`"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("⏳ عداد الحسم", callback_data="t"), InlineKeyboardButton("🏆 العمالقة", callback_data="l")],
            [InlineKeyboardButton("✨ جرعة تفاؤل", callback_data="i"), InlineKeyboardButton("📊 ملفي", callback_data="s")]
        ]
        await update.message.reply_text(f"🏰 **أهلاً بك في عرين الإمبراطور {update.effective_user.first_name}**\n\nاكتب (ملفي) أو (كم تبقى للباك) أو استخدم الأزرار:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def chat_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text: return
        text = update.message.text.lower()
        user = update.effective_user

        # زيادة XP تلقائياً
        conn = sqlite3.connect("hamza_pro_v2.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.execute("UPDATE users SET xp = xp + 1 WHERE id = ?", (user.id,))
        conn.commit()
        conn.close()

        # الرد الذكي على الكلمات
        if any(word in text for word in ["عداد الحسم", "كم تبقى للباك", "كم باقي", "وقت الباك"]):
            await update.message.reply_text(self.get_timer(), parse_mode="Markdown")
        
        elif any(word in text for word in ["ملفي", "نشاطي", "نقاطي", "مستوايا"]):
            await update.message.reply_text(self.get_status(user.id, user.first_name), parse_mode="Markdown")
        
        elif "العمالقة" in text or "الترتيب" in text:
            conn = sqlite3.connect("hamza_pro_v2.db")
            top = conn.execute("SELECT name, xp FROM users ORDER BY xp DESC LIMIT 5").fetchall()
            msg = "🏆 **قائمة نخبة المجموعة:**\n\n"
            for i, u in enumerate(top): msg += f"{['🥇','🥈','🥉','✨','✨'][i]} {u[0]} — `{u[1]} XP`\n"
            await update.message.reply_text(msg, parse_mode="Markdown")
            
        elif "تفاؤل" in text or "نصيحة" in text:
            await update.message.reply_text(f"🌟 {random.choice(MOTIVATION)}", parse_mode="Markdown")

    async def button_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == "t": await query.edit_message_text(self.get_timer(), parse_mode="Markdown")
        elif query.data == "s": await query.edit_message_text(self.get_status(query.from_user.id, query.from_user.first_name), parse_mode="Markdown")
        elif query.data == "i": await query.edit_message_text(f"🌟 {random.choice(MOTIVATION)}", parse_mode="Markdown")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.button_logic))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat_logic))

    def run(self):
        threading.Thread(target=run_keep_alive, daemon=True).start()
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    UltimateHamzaBot().run()
