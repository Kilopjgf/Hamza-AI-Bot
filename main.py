import os, sqlite3, json, random, time, logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont # للمميزات البصرية والشهادات

# ==================== الإعدادات الأساسية ====================
TOKEN = "8518151371:AAGDgSVHeOK6kjYfCweFr6XfiKBEi1biltM"
GROUP_ID = -1003531785043
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # للذكاء الاصطناعي
BAC_DATE = datetime(2026, 6, 15) # موعد تقديري للباك

# ==================== قاعدة البيانات المركزية ====================
def init_db():
    conn = sqlite3.connect("study_empire.db")
    c = conn.cursor()
    # جدول المستخدمين المطور
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, streak INTEGER DEFAULT 0, last_active DATE,
        team_id INTEGER, role TEXT DEFAULT 'طالب')''')
    # جدول الفرق
    c.execute('''CREATE TABLE IF NOT EXISTS teams (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT, team_name TEXT, 
        team_code TEXT, leader_id INTEGER, total_xp INTEGER DEFAULT 0, logo_text TEXT)''')
    conn.commit()
    conn.close()

# ==================== محرك الرسوميات (الشهادات والبطاقات) ====================
def generate_cert(name, subject, score):
    img = Image.new('RGB', (800, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # رسم إطار ملكي
    draw.rectangle([20, 20, 780, 480], outline=(184, 134, 11), width=10)
    draw.text((300, 50), "شهادة تميز علمي", fill=(0, 0, 0))
    draw.text((100, 200), f"يمنح بوت حمزة الذكي هذه الشهادة لـ: {name}", fill=(0, 0, 0))
    draw.text((100, 260), f"لتفوقه في مادة: {subject} بنتيجة: {score}", fill=(0, 0, 0))
    path = f"cert_{name}.png"
    img.save(path)
    return path

# ==================== المنطق البرمجي للبوت ====================
class StudyEmpire:
    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        init_db()
        self._load_handlers()

    def _load_handlers(self):
        self.app.add_handler(CommandHandler("start", self.main_menu))
        self.app.add_handler(CallbackQueryHandler(self.button_manager))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.anti_cheat_engine))

    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # حساب العد التنازلي للباك
        remaining = BAC_DATE - datetime.now()
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("🔢 الرياضيات", callback_data="sub_math"), InlineKeyboardButton("⚛️ الفيزياء", callback_data="sub_phys")],
            [InlineKeyboardButton("👥 نظام الفرق", callback_data="team_menu"), InlineKeyboardButton("🏆 لوحة الشرف", callback_data="leaderboard")],
            [InlineKeyboardButton("📊 ملفي الشخصي", callback_data="my_profile"), InlineKeyboardButton("🤖 مساعد AI", callback_data="ai_help")]
        ]
        
        text = (f"🏰 **مرحباً بك في إمبراطورية حمزة التعليمية**\n\n"
                f"👤 الطالب: {user.first_name}\n"
                f"📅 متبقي للباك: {remaining.days} يوم\n"
                f"🔥 السلسلة الحالية: 3 أيام متتالية\n\n"
                f"اختر قسمك لبدء الرحلة 👇")
        
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def button_manager(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        await query.answer()

        if data == "sub_math":
            await self.show_subject_menu(query, "الرياضيات")
        elif data == "team_menu":
            await self.show_team_menu(query)
        elif data == "leaderboard":
            await self.show_honor_roll(query)
        elif data == "my_profile":
            await self.show_profile(query)
        elif data == "back_to_main":
            await self.main_menu(update, context)

    async def show_subject_menu(self, query, subject):
        keyboard = [
            [InlineKeyboardButton("📝 تحدي سريع", callback_data=f"quiz_{subject}"), InlineKeyboardButton("📚 ملخصات", callback_data=f"pdf_{subject}")],
            [InlineKeyboardButton("🔙 العودة للمنصة", callback_data="back_to_main")]
        ]
        await query.edit_message_text(f"🎯 قسم {subject}:\nجاهز للتحدي يا بطل؟", reply_markup=InlineKeyboardMarkup(keyboard))

    async def show_team_menu(self, query):
        keyboard = [
            [InlineKeyboardButton("➕ إنشاء فريق", callback_data="create_team"), InlineKeyboardButton("🤝 انضمام لكود", callback_data="join_team")],
            [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]
        ]
        await query.edit_message_text("⚔️ نظام تحالفات الفرق:\nاتحد مع أصدقائك لسحق البكالوريا!", reply_markup=InlineKeyboardMarkup(keyboard))

    async def show_honor_roll(self, query):
        # مثال لبيانات من قاعدة البيانات
        text = "🏅 **لوحة الشرف الأسبوعية (Top 10)**\n\n"
        text += "1️⃣ حمزة الملك - 5400 XP\n2️⃣ أحمد المتفوق - 4900 XP\n..."
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def anti_cheat_engine(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # خوارزمية بسيطة لمنع النسخ أو الإجابة بسرعة غير بشرية
        if len(update.message.text) > 500: # رسائل طويلة جداً مشبوهة
             await update.message.delete()
             await update.message.reply_text("🛡️ حماية: يمنع لصق النصوص الطويلة.")

    def run(self):
        print("🚀 إمبراطورية حمزة (StudySmart V5) قيد التشغيل...")
        self.app.run_polling()

if __name__ == "__main__":
    StudyEmpire().run()
