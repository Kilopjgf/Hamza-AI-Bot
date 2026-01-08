import os, asyncio, logging, random, json, time, hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode, ChatAction
from groq import Groq
import aiosqlite

# ==================== التهيئة الأساسية ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== قاعدة البيانات ====================
async def init_database():
    """تهيئة قاعدة البيانات"""
    async with aiosqlite.connect("empire.db") as db:
        # جدول المستخدمين
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                daily_streak INTEGER DEFAULT 0,
                last_active DATE,
                behavior_score INTEGER DEFAULT 100,
                group_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول التحديات
        await db.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                question TEXT,
                answer TEXT,
                points INTEGER,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المجموعات
        await db.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_name TEXT,
                admin_id INTEGER,
                total_xp INTEGER DEFAULT 0,
                member_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

# ==================== نظام البطاقات ====================
class CardSystem:
    """نظام البطاقات الصفراء والحمراء"""
    
    def __init__(self):
        self.cards_db = {}
        
    async def give_card(self, user_id: int, card_type: str, reason: str):
        """منح بطاقة للمستخدم"""
        if user_id not in self.cards_db:
            self.cards_db[user_id] = {'yellow': [], 'red': []}
        
        card_data = {
            'type': card_type,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        if card_type == 'yellow':
            self.cards_db[user_id]['yellow'].append(card_data)
            # إذا كان لديه 3 بطاقات صفراء، تتحول لحمراء
            if len(self.cards_db[user_id]['yellow']) >= 3:
                await self.give_card(user_id, 'red', '3 بطاقات صفراء')
                self.cards_db[user_id]['yellow'] = []
        else:
            self.cards_db[user_id]['red'].append(card_data)
        
        return card_data
    
    async def get_user_cards(self, user_id: int) -> Dict:
        """الحصول على بطاقات المستخدم"""
        return self.cards_db.get(user_id, {'yellow': [], 'red': []})

# ==================== نظام مكافحة الغش ====================
class AntiCheatSystem:
    """نظام ذكي لمكافحة الغش"""
    
    def __init__(self):
        self.suspicion_levels = {}
        self.last_answers = {}
        
    async def analyze_answer(self, user_id: int, answer_time: float, answer: str) -> Dict:
        """تحليل الإجابة للكشف عن الغش"""
        score = 0
        reasons = []
        
        # تحليل السرعة
        if answer_time < 2:
            score += 30
            reasons.append("سرعة إجابة غير طبيعية")
        
        # تحليل التشابه مع الإجابات السابقة
        if user_id in self.last_answers:
            if answer == self.last_answers[user_id]:
                score += 20
                reasons.append("تكرار الإجابة نفسها")
        
        self.last_answers[user_id] = answer
        
        # تحديث مستوى الشبهة
        if user_id not in self.suspicion_levels:
            self.suspicion_levels[user_id] = 0
        
        self.suspicion_levels[user_id] += score
        
        # تحديد الإجراء
        action = self._determine_action(self.suspicion_levels[user_id])
        
        return {
            'score': score,
            'total_score': self.suspicion_levels[user_id],
            'reasons': reasons,
            'action': action
        }
    
    def _determine_action(self, score: int) -> str:
        """تحديد الإجراء المناسب"""
        if score >= 90:
            return "تدخل مشرف"
        elif score >= 65:
            return "منع التحديات"
        elif score >= 50:
            return "خصم نقاط"
        elif score >= 30:
            return "تغيير الأسئلة"
        else:
            return "مراقبة"

# ==================== توليد الأسئلة الذكي ====================
class QuestionGenerator:
    """توليد أسئلة ذكية"""
    
    def __init__(self, groq_client=None):
        self.groq = groq_client
        self.subjects = {
            "رياضيات": ["جبر", "هندسة", "تفاضل", "تكافل"],
            "علوم": ["فيزياء", "كيمياء", "أحياء"],
            "لغات": ["عربية", "انجليزية", "فرنسية"],
            "تاريخ": ["تاريخ قديم", "تاريخ حديث", "تاريخ الجزائر"]
        }
    
    async def generate_question(self, subject: str, difficulty: str = "متوسط") -> Dict:
        """توليد سؤال"""
        
        if subject not in self.subjects:
            subject = random.choice(list(self.subjects.keys()))
        
        topic = random.choice(self.subjects[subject])
        
        # إذا كان هناك اتصال بـ Groq، استخدم الذكاء الاصطناعي
        if self.groq:
            try:
                prompt = f"اصنع سؤال {subject} في موضوع {topic} للمستوى {difficulty}"
                response = self.groq.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                question_text = response.choices[0].message.content
            except:
                question_text = self._get_fallback_question(subject, topic)
        else:
            question_text = self._get_fallback_question(subject, topic)
        
        # إنشاء خيارات
        options = self._generate_options(subject, topic)
        
        return {
            'subject': subject,
            'topic': topic,
            'question': question_text,
            'options': options,
            'correct': random.choice(['أ', 'ب', 'ج', 'د']),
            'points': self._calculate_points(difficulty),
            'difficulty': difficulty
        }
    
    def _get_fallback_question(self, subject: str, topic: str) -> str:
        """أسئلة احتياطية"""
        questions = {
            "رياضيات": {
                "جبر": "ما هو حل المعادلة: 2س + 5 = 15؟",
                "هندسة": "ما هي مساحة المربع الذي طول ضلعه 5 سم؟"
            },
            "علوم": {
                "فيزياء": "ما هي وحدة قياس القوة؟",
                "كيمياء": "ما هو الرمز الكيميائي للذهب؟"
            }
        }
        return questions.get(subject, {}).get(topic, f"سؤال في {subject} - {topic}")

# ==================== البوت الرئيسي ====================
class EmpireBot:
    """بوت الإمبراطورية التعليمي"""
    
    def __init__(self, token: str):
        self.token = token
        self.groq_client = None
        
        # محاولة تهيئة Groq إذا كان المفتاح موجوداً
        try:
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                self.groq_client = Groq(api_key=groq_key)
                logger.info("✅ تم تهيئة Groq AI بنجاح")
        except:
            logger.warning("⚠️ لا يمكن تهيئة Groq AI")
        
        # الأنظمة
        self.card_system = CardSystem()
        self.anti_cheat = AntiCheatSystem()
        self.question_gen = QuestionGenerator(self.groq_client)
        
        # جلسات المستخدمين
        self.user_sessions = {}
        self.group_challenges = {}
        
    async def initialize(self):
        """تهيئة البوت"""
        await init_database()
        
        # إنشاء التطبيق مع rate limiting لمنع Conflict
        self.app = Application.builder() \
            .token(self.token) \
            .pool_timeout(30) \
            .connect_timeout(30) \
            .read_timeout(30) \
            .write_timeout(30) \
            .build()
        
        self._setup_handlers()
        logger.info("✅ تم تهيئة البوت بنجاح")
    
    def _setup_handlers(self):
        """إعداد معالجات الأوامر"""
        
        # الأوامر العربية الأساسية
        self.app.add_handler(CommandHandler("بدء", self.start_command))
        self.app.add_handler(CommandHandler("سؤال", self.question_command))
        self.app.add_handler(CommandHandler("نصيحة", self.advice_command))
        self.app.add_handler(CommandHandler("تحدي", self.challenge_command))
        self.app.add_handler(CommandHandler("قائمتي", self.my_list_command))
        self.app.add_handler(CommandHandler("تحدي_جماعي", self.group_challenge_command))
        self.app.add_handler(CommandHandler("المساعدة", self.help_command))
        
        # معالجة الأزرار
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # معالجة الرسائل النصية
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # معالجة رسائل المجموعات
        self.app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, self.handle_group_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البدء - /بدء"""
        user = update.effective_user
        chat = update.effective_chat
        
        # تحديث بيانات المستخدم
        async with aiosqlite.connect("empire.db") as db:
            await db.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_active) 
                VALUES (?, ?, ?, ?)
            ''', (user.id, user.username, user.first_name, datetime.now().date().isoformat()))
            await db.commit()
        
        # واجهة ترحيبية
        keyboard = [
            [
                InlineKeyboardButton("🎯 سؤال جديد", callback_data="new_question"),
                InlineKeyboardButton("💡 نصيحة ذكية", callback_data="smart_advice")
            ],
            [
                InlineKeyboardButton("⚔️ تحدي فردي", callback_data="single_challenge"),
                InlineKeyboardButton("👥 تحدي جماعي", callback_data="group_challenge")
            ],
            [
                InlineKeyboardButton("📊 قائمتي", callback_data="my_list"),
                InlineKeyboardButton("❓ المساعدة", callback_data="help")
            ]
        ]
        
        welcome_text = f"""
🏰 **مرحباً بك في إمبراطورية المعرفة، {user.first_name}!** 👑

✨ **اختر ما تريد:**
• 🎯 **سؤال جديد** - اختبر معرفتك
• 💡 **نصيحة ذكية** - نصائح تعليمية مخصصة
• ⚔️ **تحدي فردي** - مواجهة مع الذكاء الاصطناعي
• 👥 **تحدي جماعي** - منافسة مع الأصدقاء
• 📊 **قائمتي** - إحصائياتك وتقدمك

🚀 **ابدأ رحلتك التعليمية الآن!**
        """
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if chat.type in ["group", "supergroup"]:
            await update.message.reply_text(
                f"👋 أهلاً بالجميع! أنا بوت الإمبراطورية التعليمي.\n\nاستخدموا الأوامر التالية:\n/سؤال - /نصيحة - /تحدي - /تحدي_جماعي - /قائمتي",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def question_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر السؤال - /سؤال"""
        user = update.effective_user
        
        # توليد سؤال جديد
        question = await self.question_gen.generate_question("رياضيات")
        
        # حفظ في الجلسة
        if user.id not in self.user_sessions:
            self.user_sessions[user.id] = {}
        
        self.user_sessions[user.id]['current_question'] = question
        self.user_sessions[user.id]['question_time'] = time.time()
        
        # إنشاء أزرار الإجابة
        keyboard = []
        for option, text in question['options'].items():
            keyboard.append([InlineKeyboardButton(
                f"{option}) {text}",
                callback_data=f"answer_{option}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔄 سؤال آخر", callback_data="new_question")])
        
        # إرسال السؤال
        question_text = f"""
🎯 **سؤال جديد!**

📚 **المادة:** {question['subject']}
📖 **الموضوع:** {question['topic']}
⭐ **الصعوبة:** {question['difficulty']}
🏆 **النقاط:** {question['points']}

❓ **{question['question']}**

⏱️ **الوقت:** لديك 60 ثانية للإجابة
        """
        
        await update.message.reply_text(
            question_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def advice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر النصيحة - /نصيحة"""
        
        # نصائح عشوائية
        advices = [
            "📚 **نصيحة:** راجع الدروس قبل النوم، فهذا يساعد على تثبيت المعلومات!",
            "⏰ **نصيحة:** خذ استراحة 5 دقائق كل 25 دقيقة من الدراسة (تقنية بومودورو)!",
            "🧠 **نصيحة:** اشرح الدرس لشخص آخر، فهذا يؤكد فهمك له!",
            "💡 **نصيحة:** استخدم الخرائط الذهنية لتنظيم المعلومات!",
            "📝 **نصيحة:** حل تمارين متنوعة بدلاً من تكرار نفس النوع!",
            "🎯 **نصيحة:** حدد أهدافاً يومية صغيرة وقابلة للتحقيق!",
            "🚀 **نصيحة:** ابدأ بالمواد الصعبة عندما يكون ذهنك منتعشاً!"
        ]
        
        advice = random.choice(advices)
        
        keyboard = [
            [InlineKeyboardButton("🎯 اطلب سؤالاً", callback_data="new_question")],
            [InlineKeyboardButton("⚔️ ابدأ تحدياً", callback_data="single_challenge")]
        ]
        
        await update.message.reply_text(
            advice,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def challenge_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر التحدي - /تحدي"""
        
        # إنشاء تحدٍ مكون من 3 أسئلة
        challenge = {
            'questions': [],
            'current_question': 0,
            'score': 0,
            'start_time': time.time(),
            'user_id': update.effective_user.id
        }
        
        # توليد 3 أسئلة
        subjects = ["رياضيات", "علوم", "لغات"]
        for i in range(3):
            subject = random.choice(subjects)
            question = await self.question_gen.generate_question(subject)
            challenge['questions'].append(question)
        
        # حفظ التحدي
        user_id = update.effective_user.id
        self.user_sessions[user_id] = challenge
        
        # عرض السؤال الأول
        await self._send_challenge_question(update, user_id)
    
    async def _send_challenge_question(self, update: Update, user_id: int):
        """إرسال سؤال من التحدي"""
        challenge = self.user_sessions.get(user_id)
        if not challenge or challenge['current_question'] >= len(challenge['questions']):
            return
        
        question = challenge['questions'][challenge['current_question']]
        
        keyboard = []
        for option, text in question['options'].items():
            keyboard.append([InlineKeyboardButton(
                f"{option}) {text}",
                callback_data=f"challenge_answer_{option}"
            )])
        
        challenge_text = f"""
⚔️ **التحدي الفردي**

📊 **السؤال:** {challenge['current_question'] + 1}/3
🏆 **النقاط الحالية:** {challenge['score']}
⏱️ **الوقت المنقضي:** {int(time.time() - challenge['start_time'])} ثانية

❓ **السؤال:**
{question['question']}
        """
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                challenge_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                challenge_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def group_challenge_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر التحدي الجماعي - /تحدي_جماعي"""
        chat = update.effective_chat
        
        if chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("⚠️ هذا الأمر للمجموعات فقط!")
            return
        
        # إنشاء تحدي جماعي
        group_challenge = {
            'group_id': chat.id,
            'questions': [],
            'participants': {},
            'start_time': time.time(),
            'active': True,
            'duration': 300  # 5 دقائق
        }
        
        # توليد 5 أسئلة للتحدي الجماعي
        for i in range(5):
            subject = random.choice(["رياضيات", "علوم", "لغات"])
            question = await self.question_gen.generate_question(subject)
            group_challenge['questions'].append(question)
        
        # حفظ التحدي
        self.group_challenges[chat.id] = group_challenge
        
        # إعلان بدء التحدي
        keyboard = [
            [InlineKeyboardButton("✅ انضم للتحدي", callback_data="join_group_challenge")],
            [InlineKeyboardButton("🎯 ابدأ الآن", callback_data="start_group_challenge")]
        ]
        
        challenge_text = f"""
👥 **تحدي جماعي جديد!**

📋 **المعلومات:**
• 🏆 5 أسئلة متنوعة
• ⏱️ مدة 5 دقائق
• 👥 منافسة جماعية
• 🎯 نقاط جماعية

📝 **تعليمات:**
1. انضم بالتسجيل
2. ابدأ عند الجاهزية
3. أجب على الأسئلة بسرعة

🚀 **الانضمام مفتوح الآن!**
        """
        
        await update.message.reply_text(
            challenge_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def my_list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر القائمة - /قائمتي"""
        user = update.effective_user
        
        # جلب بيانات المستخدم من قاعدة البيانات
        async with aiosqlite.connect("empire.db") as db:
            # بيانات المستخدم
            cursor = await db.execute(
                "SELECT xp, level, daily_streak FROM users WHERE user_id = ?",
                (user.id,)
            )
            user_data = await cursor.fetchone()
            
            # التحديات المكتملة
            cursor = await db.execute(
                "SELECT COUNT(*) as total, SUM(points) as points FROM challenges WHERE user_id = ? AND completed = 1",
                (user.id,)
            )
            challenge_data = await cursor.fetchone()
        
        if user_data:
            xp, level, streak = user_data
            total_challenges = challenge_data[0] if challenge_data else 0
            total_points = challenge_data[1] if challenge_data and challenge_data[1] else 0
            
            # حساب التقدم للمستوى التالي
            next_level_xp = level * 1000
            progress = min(100, int((xp / next_level_xp) * 100)) if next_level_xp > 0 else 0
            
            list_text = f"""
📊 **قائمتي الشخصية**

👤 **المعلومات:**
• 🏷️ الاسم: {user.first_name}
• ⭐ النقاط: {xp}
• 📈 المستوى: {level}
• 🔥 سلسلة الحضور: {streak} يوم

🏆 **الإنجازات:**
• 🎯 التحديات المكتملة: {total_challenges}
• 💎 النقاط المجمعة: {total_points}
• 📊 التقدم: {progress}% للمستوى {level + 1}

📈 **الرسم البياني:**
{'█' * int(progress/5)}{'░' * (20 - int(progress/5))} {progress}%
            """
        else:
            list_text = "❌ لم يتم العثور على بياناتك. استخدم /بدء للبدء!"
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_list")],
            [InlineKeyboardButton("🎯 سؤال جديد", callback_data="new_question")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
        ]
        
        await update.message.reply_text(
            list_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة - /المساعدة"""
        
        help_text = """
🎯 **أوامر بوت الإمبراطورية:**

👑 **الأساسية:**
/بدء - بدء البوت والواجهة الرئيسية
/سؤال - سؤال تعليمي عشوائي
/نصيحة - نصائح تعليمية ذكية
/تحدي - تحدي فردي (3 أسئلة)
/قائمتي - قائمتك الشخصية وإحصائياتك

👥 **للمجموعات:**
/تحدي_جماعي - بدء تحدي جماعي
(يجب أن يكون البوت مشرفاً في المجموعة)

⚙️ **عامة:**
/المساعدة - عرض هذه الرسالة

🎮 **كيفية اللعب:**
1. استخدم /بدء للبدء
2. اختر نوع التحدي
3. أجب على الأسئلة
4. راقب تقدمك في /قائمتي

🚀 **نصائح سريعة:**
• أجب بسرعة لمزيد من النقاط
• حافظ على سلسلة الحضور اليومية
• شارك في التحديات الجماعية
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 جرب سؤال", callback_data="new_question")],
            [InlineKeyboardButton("⚔️ جرب تحدياً", callback_data="single_challenge")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
        ]
        
        await update.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أزرار الإنلاين"""
        query = update.callback_query
        user = query.from_user
        data = query.data
        
        await query.answer()
        
        # معالجة الأنواع المختلفة من الأزرار
        if data == "new_question":
            await self._send_random_question(query)
        
        elif data == "smart_advice":
            await self._send_random_advice(query)
        
        elif data == "single_challenge":
            await self._start_single_challenge(query)
        
        elif data == "group_challenge":
            await query.edit_message_text(
                "👥 **التحدي الجماعي:**\n\nاستخدم الأمر /تحدي_جماعي في المجموعة!",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "my_list":
            await self._show_user_list(query)
        
        elif data == "help":
            await self._show_help(query)
        
        elif data == "home":
            await self._show_home(query)
        
        elif data.startswith("answer_"):
            await self._handle_answer(query, data)
        
        elif data.startswith("challenge_answer_"):
            await self._handle_challenge_answer(query, data)
        
        elif data == "join_group_challenge":
            await self._join_group_challenge(query)
        
        elif data == "start_group_challenge":
            await self._start_group_challenge(query)
        
        elif data == "refresh_list":
            await self._refresh_user_list(query)
    
    async def _send_random_question(self, query):
        """إرسال سؤال عشوائي"""
        question = await self.question_gen.generate_question("رياضيات")
        
        user_id = query.from_user.id
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        self.user_sessions[user_id]['current_question'] = question
        self.user_sessions[user_id]['question_time'] = time.time()
        
        keyboard = []
        for option, text in question['options'].items():
            keyboard.append([InlineKeyboardButton(
                f"{option}) {text}",
                callback_data=f"answer_{option}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔄 سؤال آخر", callback_data="new_question")])
        
        question_text = f"""
🎯 **سؤال جديد!**

📚 **المادة:** {question['subject']}
📖 **الموضوع:** {question['topic']}
⭐ **الصعوبة:** {question['difficulty']}
🏆 **النقاط:** {question['points']}

❓ **{question['question']}**
        """
        
        await query.edit_message_text(
            question_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_answer(self, query, data):
        """معالجة إجابة على سؤال"""
        user = query.from_user
        answer = data.replace("answer_", "")
        
        if user.id not in self.user_sessions or 'current_question' not in self.user_sessions[user.id]:
            await query.edit_message_text("❌ انتهت صلاحية السؤال. اطلب سؤالاً جديداً!")
            return
        
        question = self.user_sessions[user.id]['current_question']
        answer_time = time.time() - self.user_sessions[user.id]['question_time']
        
        # تحليل الغش
        cheat_analysis = await self.anti_cheat.analyze_answer(user.id, answer_time, answer)
        
        # التحقق من الإجابة
        is_correct = (answer == question['correct'])
        
        # حساب النقاط مع تعديل الوقت والغش
        base_points = question['points']
        time_bonus = max(0, 10 - int(answer_time)) * 5
        cheat_penalty = cheat_analysis['score'] * 2
        
        points = base_points + time_bonus - cheat_penalty
        points = max(0, points)  # التأكد من عدم وجود نقاط سلبية
        
        # تحديث نقاط المستخدم
        async with aiosqlite.connect("empire.db") as db:
            await db.execute(
                "UPDATE users SET xp = xp + ? WHERE user_id = ?",
                (points, user.id)
            )
            
            # حفظ التحدي
            await db.execute('''
                INSERT INTO challenges (user_id, subject, question, answer, points, completed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user.id, question['subject'], question['question'], answer, points, 1))
            
            await db.commit()
        
        # إعداد رسالة النتيجة
        result_text = f"""
{'✅ **أحسنت! الإجابة صحيحة**' if is_correct else '❌ **للأسف، الإجابة خاطئة**'}

📊 **النتيجة:**
• 🎯 الإجابة الصحيحة: {question['correct']}
• ⏱️ وقت الإجابة: {answer_time:.1f} ثانية
• 💎 النقاط: {points}
• 📈 نقاط الغش: {cheat_analysis['score']}

{''.join(['⚠️ ' + reason + '\n' for reason in cheat_analysis['reasons']])}

💡 **تفسير:** {question.get('explanation', 'حاول مرة أخرى!')}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 سؤال جديد", callback_data="new_question")],
            [InlineKeyboardButton("⚔️ تحدي", callback_data="single_challenge")],
            [InlineKeyboardButton("📊 قائمتي", callback_data="my_list")]
        ]
        
        await query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        message = update.message
        user = update.effective_user
        
        # تجاهل الرسائل الطويلة جداً
        if len(message.text) > 500:
            return
        
        # إذا بدأت الرسالة بـ "سؤال" (للسؤال الذكي)
        if message.text.startswith("سؤال ") and self.groq_client:
            question = message.text[4:].strip()
            
            if len(question) < 5:
                await message.reply_text("⚠️ يرجى كتابة سؤال أكثر وضوحاً!")
                return
            
            # إرسال حالة الكتابة
            await context.bot.send_chat_action(
                chat_id=message.chat_id,
                action=ChatAction.TYPING
            )
            
            try:
                # استخدام Groq للإجابة
                response = self.groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[
                        {"role": "system", "content": "أنت معلم عربي متخصص في التعليم."},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.7
                )
                
                answer = response.choices[0].message.content
                
                # تقسيم الإجابة إذا كانت طويلة
                if len(answer) > 4000:
                    parts = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
                    await message.reply_text(f"🤖 **الجزء 1/{len(parts)}:**\n\n{parts[0]}")
                    for i, part in enumerate(parts[1:], 2):
                        await message.reply_text(f"📄 **الجزء {i}/{len(parts)}:**\n\n{part}")
                else:
                    await message.reply_text(f"🤖 **إجابة الذكاء الاصطناعي:**\n\n{answer}")
            
            except Exception as e:
                logger.error(f"خطأ في الذكاء الاصطناعي: {e}")
                await message.reply_text("❌ حدث خطأ في معالجة سؤالك. حاول مرة أخرى!")
    
    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة رسائل المجموعات"""
        message = update.message
        chat = update.effective_chat
        
        # إذا تم ذكر البوت
        if self.app.bot.username in message.text:
            reply = f"👋 أهلاً بك! أنا بوت الإمبراطورية التعليمي.\n\nاستخدم /المساعدة لرؤية الأوامر المتاحة!"
            await message.reply_text(reply)
    
    async def run(self):
        """تشغيل البوت"""
        await self.initialize()
        
        # تنظيف الجلسات القديمة بشكل دوري
        async def cleanup_sessions():
            while True:
                try:
                    current_time = time.time()
                    to_remove = []
                    
                    for user_id, session in self.user_sessions.items():
                        if 'question_time' in session:
                            if current_time - session['question_time'] > 300:  # 5 دقائق
                                to_remove.append(user_id)
                    
                    for user_id in to_remove:
                        del self.user_sessions[user_id]
                    
                    await asyncio.sleep(60)  # كل دقيقة
                except:
                    await asyncio.sleep(10)
        
        # بدء التنظيف في الخلفية
        asyncio.create_task(cleanup_sessions())
        
        # بدء البوت
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        logger.info("🚀 بوت الإمبراطورية يعمل الآن!")
        
        # الانتظار
        await self.app.updater.idle()

# ==================== التشغيل الرئيسي ====================
async def main():
    """الدالة الرئيسية"""
    
    # الحصول على التوكن من متغير البيئة
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        print("❌ خطأ: لم يتم تعيين BOT_TOKEN في متغيرات البيئة!")
        print("📝 أضف التوكن إلى ملف .env أو متغيرات البيئة")
        return
    
    # إنشاء وتشغيل البوت
    bot = EmpireBot(token)
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n👋 إيقاف البوت...")
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    # ملف requirements.txt المطلوب
    """
    python-telegram-bot[job-queue]==20.7
    groq==0.6.0
    aiosqlite==0.19.0
    python-dotenv==1.0.0
    """
    
    # ملف .env المطلوب
    """
    BOT_TOKEN=توكن_البوت_هنا
    GROQ_API_KEY=مفتاح_groq_اختياري
    """
    
    asyncio.run(main())
