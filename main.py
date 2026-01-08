import os, threading, sqlite3, logging, time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver

# --- إعدادات السيرفر الوهمي لـ Render ---
def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
BAC_DATE = datetime(2026, 6, 15)

# --- قاعدة البيانات ---
def db_manage(query, params=(), fetch=False):
    conn = sqlite3.connect("empire.db")
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data

def init_db():
    db_manage('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1)''')

# --- محرك البوت الإمبراطوري ---
class HamzaProBot:
    def __init__(self):
        init_db()
        self.app = Application.builder().token(TOKEN).build()
        self._load_handlers()

    def get_rank_info(self, xp):
        ranks = [(0, "🛡️ محارب"), (500, "⚔️ قائد"), (2000, "🎖️ جنرال"), (5000, "👑 إمبراطور")]
        current_rank = ranks[0][1]
        next_xp = 500
        for r_xp, r_name in ranks:
            if xp >= r_xp:
                current_rank = r_name
                idx = ranks.index((r_xp, r_name))
                next_xp = ranks[idx+1][0] if idx+1 < len(ranks) else xp
        
        progress = int((xp / next_xp) * 10) if next_xp != xp else 10
        bar = "▰" * progress + "▱" * (10 - progress)
        return current_rank, bar

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_manage("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        
        days_left = (BAC_DATE - datetime.now()).days
        keyboard = [
            [InlineKeyboardButton("📚 الترسانة التعليمية", callback_data="edu"), InlineKeyboardButton("🤖 مستشار AI", callback_data="ai")],
            [InlineKeyboardButton("📊 ملفي الملكي", callback_data="me"), InlineKeyboardButton("🏆 قائمة العمالقة", callback_data="top")],
            [InlineKeyboardButton("⚙️ دعم الإمبراطورية", url="https://t.me/your_username")] # ضع معرفك هنا
        ]
        
        welcome_text = (f"🏰 **أهلاً بك في إمبراطورية حمزة التعليمية**\n\n"
                        f"🎯 **الهدف:** بكالوريا 2026\n"
                        f"⏳ **متبقي:** {days_left} يوم من الكفاح\n"
                        f"✨ **الحالة:** السيرفر يعمل بأقصى سرعة\n\n"
                        f"اختر سلاحك اليوم 👇")
        
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer() # لسرعة استجابة الزر

        if query.data == "me":
            user_data = db_manage("SELECT xp, level FROM users WHERE id=?", (user_id,), fetch=True)
            xp = user_data[0][0] if user_data else 0
            rank, bar = self.get_rank_info(xp)
            
            text = (f"👤 **البطاقة الشخصية للمجاهد:**\n\n"
                    f"🎖️ **الرتبة:** {rank}\n"
                    f"⭐ **النقاط:** {xp} XP\n"
                    f"📈 **التقدم للرتبة التالية:**\n`{bar}`\n\n"
                    f"تفاعل في القروب لزيادة نقاطك!")
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")
        
        elif query.data == "home":
            # العودة للقائمة الرئيسية (إعادة بناء Start)
            await self.start(update, context)

    async def group_guard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # منع الروابط وزيادة النقاط بالتفاعل
        if not update.message or not update.message.text: return
        
        # زيادة نقاط تلقائية عند التفاعل
        db_manage("UPDATE users SET xp = xp + 1 WHERE id = ?", (update.effective_user.id,))
        
        if "http" in update.message.text.lower():
            if update.effective_user.id != 8518151371: # استثناءك أنت (الإمبراطور)
                await update.message.delete()
                await
