import os, threading, sqlite3, logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import http.server
import socketserver
from groq import Groq

# --- السيرفر الوهمي لـ Render ---
def run_keep_alive():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

# --- الإعدادات ---
TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# --- قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect("empire_final.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

class HamzaLegendBot:
    def __init__(self):
        init_db()
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        # تحديث بيانات المستخدم
        conn = sqlite3.connect("empire_final.db")
        conn.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user.id, user.first_name))
        conn.commit()
        conn.close()

        keyboard = [
            [InlineKeyboardButton("⚔️ ترسانة الدروس", callback_data="edu_hub"), InlineKeyboardButton("🧠 العقل الاصطناعي", callback_data="ai_zone")],
            [InlineKeyboardButton("🏆 ترتيب العمالقة", callback_data="leaderboard"), InlineKeyboardButton("👤 ملفي الملكي", callback_data="status")],
            [InlineKeyboardButton("🔗 انضم لقناة المجد", url="https://t.me/your_channel")]
        ]
        text = f"🏰 **مرحباً بك في عرين الإمبراطور {user.first_name}**\n\nقم باختيار وجهتك اليوم لبناء مجدك العلمي 👇"
        await (update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown") if update.message else update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"))

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        # 1. ترسانة الدروس (المكتبة المنظمة)
        if query.data == "edu_hub":
            keyboard = [
                [InlineKeyboardButton("🔢 الرياضيات", callback_data="math"), InlineKeyboardButton("⚛️ الفيزياء", callback_data="phys")],
                [InlineKeyboardButton("🧪 العلوم", callback_data="sci"), InlineKeyboardButton("📚 لغات", callback_data="lang")],
                [InlineKeyboardButton("🔙 العودة للعرين", callback_data="home")]
            ]
            await query.edit_message_text("📚 **مرحباً بك في الترسانة التعليمية**\nاختر المادة التي تريد سحقها اليوم:", reply_markup=InlineKeyboardMarkup(keyboard))

        # 2. ذكاء اصطناعي (توضيح الطريقة)
        elif query.data == "ai_zone":
            await query.edit_message_text("🤖 **العقل الاصطناعي (Groq) جاهز!**\n\nللحدث معي، فقط ابدأ رسالتك بكلمة (سؤال) متبوعة بسؤالك.\nمثال: `سؤال كيف أشتق دالة أسية؟`", 
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]))

        # 3. ترتيب العمالقة (عرض تنافسي)
        elif query.data == "leaderboard":
            conn = sqlite3.connect("empire_final.db")
            top_users = conn.execute("SELECT name, xp FROM users ORDER BY xp DESC LIMIT 5").fetchall()
            conn.close()
            
            lead_text = "🏆 **قائمة عمالقة الإمبراطورية**\n\n"
            medals = ["🥇", "🥈", "🥉", "🎖️", "🎖️"]
            for i, user in enumerate(top_users):
                lead_text += f"{medals[i]} {user[0]} — `{user[1]} XP` \n"
            
            await query.edit_message_text(lead_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]), parse_mode="Markdown")

        elif query.data == "status":
            conn = sqlite3.connect("empire_final.db")
            res = conn.execute("SELECT xp FROM users WHERE id=?", (query.from_user.id,)).fetchone()
            xp = res[0] if res else 0
            await query.edit_message_text(f"👤 **ملفك الملكي:**\n\n⭐ **نقاطك:** {xp} XP\n\nاستمر في التفاعل لرفع ترتيبك!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data="home")]]))

        elif query.data == "home":
            await self.start(update, context)

    async def chat_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text: return
        text = update.message.text
        user_id = update.effective_user.id

        # زيادة نقاط التفاعل
        conn = sqlite3.connect("empire_final.db")
        conn.execute("UPDATE users SET xp = xp + 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        # معالجة سؤال الذكاء الاصطناعي
        if text.startswith("سؤال"):
            prompt = text.replace("سؤال", "").strip()
            waiting_msg = await update.message.reply_text("🌀 جاري استدعاء العقل الاصطناعي...")
            try:
                client = Groq(api_key=GROQ_KEY)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-70b-8192",
                )
                await waiting_msg.edit_text(f"🤖 **إجابة العقل الاصطناعي:**\n\n{chat_completion.choices[0].message.content}")
            except:
                await waiting_msg.edit_text("❌ حدث خطأ في الاتصال بالعقل. تأكد من مفتاح Groq.")

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat_logic))

    def run(self):
        threading.Thread(target=run_keep_alive, daemon=True).start()
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    HamzaLegendBot().run()
