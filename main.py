import os, asyncio, sqlite3, logging, random, json, time, hashlib
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode, ChatAction
from groq import Groq
import aiosqlite
import re

# ==================== التهيئة الأساسية ====================
TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== نظام البطاقات الصفراء والحمراء ====================
class CardType(Enum):
    YELLOW = "🟡 بطاقة صفراء"
    RED = "🔴 بطاقة حمراء"
    GREEN = "🟢 بطاقة خضراء"

class BehaviorSystem:
    """نظام إدارة سلوك الطلاب بالبطاقات الملونة"""
    
    def __init__(self):
        self.cards_log = {}  # {user_id: [(type, reason, date)]}
        self.warnings_cache = {}  # {user_id: warning_count}
        
    async def issue_card(self, user_id: int, card_type: CardType, reason: str, admin_id: Optional[int] = None) -> Dict:
        """إصدار بطاقة للمستخدم"""
        
        if user_id not in self.cards_log:
            self.cards_log[user_id] = []
        
        card_data = {
            'type': card_type,
            'reason': reason,
            'timestamp': datetime.now(),
            'issuer': admin_id or 'system',
            'card_id': hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:8]
        }
        
        self.cards_log[user_id].append(card_data)
        
        # تحديث قاعدة البيانات
        async with aiosqlite.connect("empire_pro.db") as db:
            await db.execute('''
                INSERT OR IGNORE INTO user_cards (user_id, card_type, reason, issuer, card_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, card_type.value, reason, str(card_data['issuer']), card_data['card_id']))
            await db.commit()
        
        # التحقق من العقوبات التلقائية
        penalties = await self._check_penalties(user_id)
        
        return {
            'success': True,
            'card_data': card_data,
            'total_yellows': self._count_cards(user_id, CardType.YELLOW),
            'total_reds': self._count_cards(user_id, CardType.RED),
            'penalties': penalties,
            'message': self._generate_card_message(user_id, card_type, reason)
        }
    
    def _count_cards(self, user_id: int, card_type: CardType) -> int:
        """عد البطاقات من نوع معين"""
        if user_id not in self.cards_log:
            return 0
        return sum(1 for card in self.cards_log[user_id] if card['type'] == card_type)
    
    async def _check_penalties(self, user_id: int) -> List[str]:
        """فحص العقوبات التلقائية بناءً على البطاقات"""
        penalties = []
        yellows = self._count_cards(user_id, CardType.YELLOW)
        reds = self._count_cards(user_id, CardType.RED)
        
        # قاعدة البطاقات الصفراء
        if yellows >= 3:
            penalties.append("⏳ حظر مؤقت لمدة 24 ساعة (3 بطاقات صفراء)")
        
        if reds >= 1:
            penalties.append("🚫 تقليل النقاط بنسبة 50% لمدة أسبوع")
        
        if reds >= 2:
            penalties.append("⚡ حظر من التحديات الجماعية لمدة أسبوع")
        
        if yellows >= 5 or reds >= 3:
            penalties.append("👑 إرسال تنبيه للمشرف لمراجعة الحساب")
        
        return penalties
    
    def _generate_card_message(self, user_id: int, card_type: CardType, reason: str) -> str:
        """توليد رسالة البطاقة"""
        base_messages = {
            CardType.YELLOW: [
                "⚠️ تنبيه! لاحظنا سلوكاً غير ملائم.",
                "🟡 انتبه! هذا السلوك قد يؤدي لعقوبات.",
                "📝 تحذير: حاول الالتزام بقواعد الإمبراطورية."
            ],
            CardType.RED: [
                "🔴 مخالفة جسيمة! تم تسجيل البطاقة الحمراء.",
                "⛔ سلوك غير مقبول وقد يؤثر على مشاركتك.",
                "🚨 انتبه! البطاقات الحمراء لها عواقب كبيرة."
            ],
            CardType.GREEN: [
                "🟢 ممتاز! سلوك إيجابي تم تسجيله.",
                "🌟 أحسنت! لقد أظهرت التزاماً رائعاً.",
                "🏅 شكراً لكونك نموذجاً يُحتذى به."
            ]
        }
        
        message = random.choice(base_messages[card_type])
        
        if card_type == CardType.YELLOW:
            yellows = self._count_cards(user_id, CardType.YELLOW)
            message += f"\n📊 لديك الآن {yellows} بطاقة صفراء"
            if yellows >= 2:
                message += f"\n⚡ تحذير: {3-yellows} بطاقات صفراء تفصلك عن عقوبة!"
        
        elif card_type == CardType.RED:
            reds = self._count_cards(user_id, CardType.RED)
            message += f"\n📊 لديك الآن {reds} بطاقة حمراء"
        
        message += f"\n📝 السبب: {reason}"
        return message
    
    async def get_user_cards_display(self, user_id: int) -> str:
        """الحصول على عرض بصري للبطاقات"""
        if user_id not in self.cards_log or not self.cards_log[user_id]:
            return "✅ لا توجد بطاقات مسجلة"
        
        display = "📋 **سجل البطاقات:**\n\n"
        
        yellows = self._count_cards(user_id, CardType.YELLOW)
        reds = self._count_cards(user_id, CardType.RED)
        greens = self._count_cards(user_id, CardType.GREEN)
        
        # عرض بصري للبطاقات
        if yellows > 0:
            display += f"🟡 **البطاقات الصفراء:** {yellows}\n"
            for i, card in enumerate([c for c in self.cards_log[user_id] if c['type'] == CardType.YELLOW][-3:], 1):
                display += f"  {i}. {card['reason']} ({card['timestamp'].strftime('%Y-%m-%d')})\n"
        
        if reds > 0:
            display += f"\n🔴 **البطاقات الحمراء:** {reds}\n"
            for i, card in enumerate([c for c in self.cards_log[user_id] if c['type'] == CardType.RED], 1):
                display += f"  {i}. {card['reason']} ({card['timestamp'].strftime('%Y-%m-%d')})\n"
        
        if greens > 0:
            display += f"\n🟢 **البطاقات الخضراء:** {greens}\n"
        
        # حالة العقوبات الحالية
        penalties = await self._check_penalties(user_id)
        if penalties:
            display += "\n⚖️ **العقوبات النشطة:**\n"
            for penalty in penalties:
                display += f"• {penalty}\n"
        
        return display

# ==================== نظام مكافحة الغش الذكي ====================
class AntiCheatSystem:
    """نظام ذكي للكشف عن الغش بإجراءات متدرجة"""
    
    def __init__(self):
        self.cheat_scores = {}  # {user_id: score}
        self.behavior_patterns = {}  # {user_id: [patterns]}
        self.suspicion_history = {}  # {user_id: [events]}
        self.behavior_system = BehaviorSystem()
        
        # مستويات الغش والإجراءات
        self.levels = {
            1: {"min": 0, "max": 29, "icon": "✅", "action": "طبيعي", "color": "green"},
            2: {"min": 30, "max": 49, "icon": "🟡", "action": "تغيير الأسئلة", "color": "yellow"},
            3: {"min": 50, "max": 64, "icon": "🟠", "action": "خصم 30% نقاط", "color": "orange"},
            4: {"min": 65, "max": 79, "icon": "🔴", "action": "منع التحديات", "color": "red"},
            5: {"min": 80, "max": 89, "icon": "⛔", "action": "حظر مؤقت", "color": "darkred"},
            6: {"min": 90, "max": 100, "icon": "🚫", "action": "تدخل مشرف", "color": "black"}
        }
    
    async def analyze_activity(self, user_id: int, activity_data: Dict) -> Dict:
        """تحليل النشاط للكشف عن الغش"""
        
        score = 0
        detected_patterns = []
        
        # 1. تحليل سرعة الإجابة
        time_score = self._analyze_answer_time(activity_data.get('answer_time', 0), 
                                               activity_data.get('question_difficulty', 'medium'))
        if time_score > 0:
            score += time_score
            detected_patterns.append("سرعة إجابة غير طبيعية")
        
        # 2. اكتشاف الأنماط
        pattern_score = self._detect_cheating_patterns(activity_data.get('answer_pattern', ''))
        if pattern_score > 0:
            score += pattern_score
            detected_patterns.append("نمط إجابات مشبوه")
        
        # 3. تحليل الدقة
        accuracy_score = self._analyze_accuracy(activity_data.get('accuracy', 0), 
                                                activity_data.get('historical_accuracy', 50))
        if accuracy_score > 0:
            score += accuracy_score
            detected_patterns.append("تغير مفاجئ في الدقة")
        
        # 4. اكتشاف النسخ
        copy_score = self._detect_copying(activity_data.get('answer_text', ''), 
                                          activity_data.get('similarity_score', 0))
        if copy_score > 0:
            score += copy_score
            detected_patterns.append("مؤشرات نسخ")
        
        # تحديث الدرجة التراكمية
        cumulative_score = self._update_cumulative_score(user_id, score)
        
        # تحديد مستوى الغش
        level = self._determine_level(cumulative_score)
        level_info = self.levels[level]
        
        # تسجيل التاريخ
        self._log_suspicion(user_id, {
            'score': score,
            'cumulative': cumulative_score,
            'patterns': detected_patterns,
            'level': level,
            'timestamp': datetime.now()
        })
        
        # إصدار بطاقات تلقائية حسب المستوى
        if level >= 3:  # من المستوى 3 فما فوق
            card_type = CardType.YELLOW if level <= 4 else CardType.RED
            await self.behavior_system.issue_card(
                user_id, 
                card_type, 
                f"نشاط مشبوه - مستوى {level}: {', '.join(detected_patterns[:2])}"
            )
        
        # إنشاء التقرير
        report = {
            'score': score,
            'cumulative_score': cumulative_score,
            'level': level,
            'level_icon': level_info['icon'],
            'level_action': level_info['action'],
            'detected_patterns': detected_patterns,
            'recommended_action': self._get_recommended_action(level, cumulative_score),
            'visual_indicator': self._create_visual_indicator(cumulative_score),
            'next_threshold': self._get_next_threshold(level),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _analyze_answer_time(self, answer_time: float, difficulty: str) -> int:
        """تحليل سرعة الإجابة"""
        time_thresholds = {
            'easy': {'suspicious': 2, 'cheating': 1},
            'medium': {'suspicious': 5, 'cheating': 2},
            'hard': {'suspicious': 8, 'cheating': 3}
        }
        
        threshold = time_thresholds.get(difficulty, time_thresholds['medium'])
        
        if answer_time <= threshold['cheating']:
            return 40  # غش مؤكد
        elif answer_time <= threshold['suspicious']:
            return 20  # مشبوه
        return 0
    
    def _detect_cheating_patterns(self, pattern: str) -> int:
        """اكتشاف أنماط الغش في الإجابات"""
        if len(pattern) < 4:
            return 0
        
        score = 0
        
        # النمط المتكرر (مثل AAAA أو ABCDABCD)
        if self._is_repeating_pattern(pattern):
            score += 30
        
        # النمط الخطي (مثل ABCD أو DCBA)
        if self._is_linear_pattern(pattern):
            score += 20
        
        # تكرار نفس الإجابة
        if len(set(pattern)) == 1:
            score += 25
        
        return score
    
    def _is_repeating_pattern(self, pattern: str) -> bool:
        """اكتشاف النمط المتكرر"""
        for i in range(1, len(pattern)//2 + 1):
            if len(pattern) % i == 0:
                segment = pattern[:i]
                if pattern == segment * (len(pattern) // i):
                    return True
        return False
    
    def _is_linear_pattern(self, pattern: str) -> bool:
        """اكتشاف النمط الخطي"""
        # تحويل الأحرف إلى أرقام
        try:
            nums = [ord(c.upper()) - 65 for c in pattern if c.isalpha()]
            if len(nums) < 3:
                return False
            
            # التحقق إذا كان تقدمًا حسابيًا
            diff = nums[1] - nums[0]
            for i in range(2, len(nums)):
                if nums[i] - nums[i-1] != diff:
                    return False
            return True
        except:
            return False
    
    def _create_visual_indicator(self, score: int) -> str:
        """إنشاء مؤشر بصري لمستوى الغش"""
        indicators = {
            range(0, 30): "🟢 [═══════════════] 0-29% (آمن)",
            range(30, 50): "🟡 [███════════════] 30-49% (مراقبة)",
            range(50, 65): "🟠 [██████═════════] 50-64% (تحذير)",
            range(65, 80): "🔴 [█████████══════] 65-79% (خطر)",
            range(80, 90): "⛔ [████████████═══] 80-89% (خطر عال)",
            range(90, 101): "🚫 [███████████████] 90-100% (حرج)"
        }
        
        for rng, indicator in indicators.items():
            if score in rng:
                return indicator
        return indicators[range(0, 30)]
    
    def _get_recommended_action(self, level: int, score: int) -> str:
        """الحصول على الإجراء الموصى به"""
        actions = {
            1: "المتابعة الطبيعية",
            2: "تغيير صيغة الأسئلة",
            3: "تقليل النقاط + إشعار",
            4: "منع التحديات لمدة ساعة",
            5: "حظر 24 ساعة + مراجعة",
            6: "تجميد الحساب + تدخل مشرف"
        }
        return actions.get(level, "تحليل إضافي")
    
    def _get_next_threshold(self, current_level: int) -> str:
        """الحصول على العتبة التالية"""
        if current_level < 6:
            next_level = current_level + 1
            threshold = self.levels[next_level]['min']
            return f"{threshold}% للوصول للمستوى {next_level}"
        return "الحد الأقصى"

# ==================== نظام توليد الأسئلة الذكي ====================
class SmartQuestionGenerator:
    """نظام توليد أسئلة ذكية مقاومة للغش"""
    
    def __init__(self, groq_client):
        self.groq = groq_client
        self.question_cache = {}  # لتجنب التكرار
        self.user_question_history = {}  {user_id: [question_ids]}
        
        # قواعد الأسئلة المقاومة للغش
        self.anti_cheat_rules = {
            'randomize_options': True,
            'dynamic_values': True,
            'context_variation': True,
            'multi_step': False,
            'time_based': False
        }
    
    async def generate_smart_question(self, user_id: int, subject: str, difficulty: str, anti_cheat_level: int = 1) -> Dict:
        """توليد سؤال ذكي مقاوم للغش"""
        
        # تحديد قواعد مقاومة الغش بناءً على المستوى
        rules = self._adjust_anti_cheat_rules(anti_cheat_level)
        
        # بناء الـ prompt الذكي
        prompt = self._build_anti_cheat_prompt(subject, difficulty, rules, user_id)
        
        try:
            # توليد السؤال باستخدام Groq AI
            response = self.groq.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "أنت خبير في صياغة أسئلة تعليمية مقاومة للغش."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7 + (anti_cheat_level * 0.05),  # زيادة العشوائية للمستويات العالية
                max_tokens=800
            )
            
            # تحليل الاستجابة
            question_data = self._parse_question_response(response.choices[0].message.content)
            
            # تطبيق قواعد مقاومة الغش
            question_data = self._apply_anti_cheat_features(question_data, rules)
            
            # إضافة معلومات التتبع
            question_data.update({
                'question_id': hashlib.md5(f"{user_id}{subject}{time.time()}".encode()).hexdigest()[:10],
                'generated_at': datetime.now().isoformat(),
                'anti_cheat_level': anti_cheat_level,
                'rules_applied': list(rules.keys()),
                'personalized': True,
                'cache_key': self._generate_cache_key(user_id, subject, difficulty)
            })
            
            # التخزين في الذاكرة المؤقتة
            if user_id not in self.user_question_history:
                self.user_question_history[user_id] = []
            self.user_question_history[user_id].append(question_data['question_id'])
            
            # حفظ في قاعدة البيانات
            await self._save_question_to_db(user_id, question_data)
            
            return question_data
            
        except Exception as e:
            logger.error(f"خطأ في توليد السؤال: {e}")
            return await self._generate_fallback_question(subject, difficulty, anti_cheat_level)
    
    def _build_anti_cheat_prompt(self, subject: str, difficulty: str, rules: Dict, user_id: int) -> str:
        """بناء أمر توليد السؤال المقاوم للغش"""
        
        rule_descriptions = []
        if rules.get('randomize_options'):
            rule_descriptions.append("ترتيب الخيارات عشوائي وغير متوقع")
        if rules.get('dynamic_values'):
            rule_descriptions.append("القيم الرقمية تتغير في كل مرة")
        if rules.get('context_variation'):
            rule_descriptions.append("سياق السؤال متغير وشخصي")
        if rules.get('multi_step'):
            rule_descriptions.append("السؤال متعدد الخطوات")
        if rules.get('time_based'):
            rule_descriptions.append("يتضمن عنصراً زمنياً")
        
        prompt = f"""
        أنت معلم {subject} محترف. قم بإنشاء سؤال تعليمي بمتطلبات محددة:
        
        **الموضوع:** {subject}
        **المستوى:** {difficulty}
        **مقاومة الغش:** مستوى {len(rule_descriptions)}/5
        **التقنيات المضادة:** {', '.join(rule_descriptions)}
        
        **متطلبات السؤال:**
        1. السؤال أصلي وغير موجود على الإنترنت
        2. مناسب للطلاب العرب في المرحلة الثانوية
        3. يحتوي على 4 خيارات للإجابة (أ، ب، ج، د)
        4. يتضمن خطوات حل مبسطة
        5. له قيمة تعليمية واضحة
        
        **مقاومة الغش المطلوبة:**
        - لا يمكن حله بالبحث المباشر
        - يتطلب فهم حقيقي للمفاهيم
        - الخيارات مضللة ولكن عادلة
        - الإجابة تحتاج تفكير وليس حفظ
        
        **تنسيق الإخراج الدقيق:**
        ||السؤال||: [نص السؤال هنا]
        ||الخيارات||: [أ) الخيار الأول | ب) الخيار الثاني | ج) الخيار الثالث | د) الخيار الرابع]
        ||الإجابة||: [حرف الخيار الصحيح فقط]
        ||التوضيح||: [شرح مفصل للإجابة]
        ||النقاط||: [عدد النقاط من 10-100]
        ||المستوى||: [سهل/متوسط/صعب]
        ||الوقت||: [الوقت المقترد بالثواني]
        """
        
        return prompt
    
    def _apply_anti_cheat_features(self, question_data: Dict, rules: Dict) -> Dict:
        """تطبيق ميزات مقاومة الغش على السؤال"""
        
        if rules.get('randomize_options') and 'options' in question_data:
            options = question_data['options']
            correct_answer = question_data['answer']
            
            # حفظ الخيار الصحيح
            correct_text = options.get(correct_answer, '')
            
            # خلط الخيارات
            option_keys = list(options.keys())
            random.shuffle(option_keys)
            
            # إنشاء تخطيط جديد
            new_options = {}
            letter_map = {}
            
            for i, key in enumerate(option_keys):
                new_letter = chr(65 + i)  # A, B, C, D
                new_options[new_letter] = options[key]
                if key == correct_answer:
                    question_data['answer'] = new_letter
                    letter_map[correct_answer] = new_letter
            
            question_data['options'] = new_options
            question_data['letter_map'] = letter_map
        
        if rules.get('dynamic_values') and 'question_text' in question_data:
            # استبدال القيم الرقمية بقيم ديناميكية
            text = question_data['question_text']
            numbers = re.findall(r'\b\d+\b', text)
            
            for num in set(numbers):
                if int(num) < 100:  # استبدال الأرقام الصغيرة فقط
                    new_num = random.randint(int(num)-2, int(num)+2)
                    new_num = max(1, new_num)  # تجنب الأرقام السالبة
                    text = text.replace(num, str(new_num))
            
            question_data['question_text'] = text
            question_data['dynamic_values_applied'] = True
        
        return question_data
    
    def _adjust_anti_cheat_rules(self, level: int) -> Dict:
        """ضبط قواعد مقاومة الغش حسب المستوى"""
        rules = self.anti_cheat_rules.copy()
        
        if level >= 2:
            rules['dynamic_values'] = True
        
        if level >= 3:
            rules['context_variation'] = True
        
        if level >= 4:
            rules['multi_step'] = True
        
        if level >= 5:
            rules['time_based'] = True
        
        return rules

# ==================== البوت الرئيسي المحدث ====================
class HamzaEmpireProBot:
    """بوت الإمبراطورية التعليمي المتكامل"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.behavior_system = BehaviorSystem()
        self.anti_cheat = AntiCheatSystem()
        self.question_gen = SmartQuestionGenerator(self.groq_client) if self.groq_client else None
        
        # إعدادات البوت
        self.user_sessions = {}
        self.active_challenges = {}
        
    async def init_bot(self):
        """تهيئة البوت"""
        await self._init_database()
        self.app = Application.builder().token(TOKEN).build()
        self._setup_handlers()
        
        logger.info("🏰 بوت الإمبراطورية التعليمي جاهز للعمل!")
    
    async def _init_database(self):
        """تهيئة قاعدة البيانات"""
        async with aiosqlite.connect("empire_pro.db") as db:
            # الجداول الأساسية
            await db.execute('''CREATE TABLE IF NOT EXISTS users 
                             (id INTEGER PRIMARY KEY, 
                              name TEXT, 
                              xp INTEGER DEFAULT 0,
                              level INTEGER DEFAULT 1,
                              daily_streak INTEGER DEFAULT 0,
                              last_active DATE,
                              behavior_score INTEGER DEFAULT 100,
                              cheat_level INTEGER DEFAULT 0,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # جدول البطاقات
            await db.execute('''CREATE TABLE IF NOT EXISTS user_cards
                             (card_id INTEGER PRIMARY KEY AUTOINCREMENT,
                              user_id INTEGER,
                              card_type TEXT,
                              reason TEXT,
                              issuer TEXT,
                              card_hash TEXT UNIQUE,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # جدول نشاط الغش
            await db.execute('''CREATE TABLE IF NOT EXISTS cheat_logs
                             (log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                              user_id INTEGER,
                              cheat_score INTEGER,
                              detected_patterns TEXT,
                              action_taken TEXT,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # جدول الأسئلة المولدة
            await db.execute('''CREATE TABLE IF NOT EXISTS ai_questions
                             (question_id TEXT PRIMARY KEY,
                              user_id INTEGER,
                              subject TEXT,
                              difficulty TEXT,
                              question_text TEXT,
                              options TEXT,
                              correct_answer TEXT,
                              explanation TEXT,
                              anti_cheat_level INTEGER,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            await db.commit()
    
    def _setup_handlers(self):
        """إعداد معالجات الأوامر"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("cards", self.show_cards_command))
        self.app.add_handler(CommandHandler("behavior", self.behavior_report_command))
        self.app.add_handler(CommandHandler("challenge", self.smart_challenge_command))
        self.app.add_handler(CommandHandler("profile", self.user_profile_command))
        
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البدء"""
        user = update.effective_user
        
        # تسجيل المستخدم
        async with aiosqlite.connect("empire_pro.db") as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)",
                (user.id, user.first_name or user.username)
            )
            await db.commit()
        
        # إنشاء واجهة البداية
        keyboard = [
            [InlineKeyboardButton("🧠 تحديات ذكية", callback_data="smart_challenges"),
             InlineKeyboardButton("📊 ملف السلوك", callback_data="behavior_profile")],
            [InlineKeyboardButton("⚔️ تحديات مقاومة", callback_data="anti_cheat_challenges"),
             InlineKeyboardButton("🏆 ترتيب", callback_data="leaderboard")],
            [InlineKeyboardButton("🛡️ بطاقاتي", callback_data="my_cards"),
             InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")]
        ]
        
        welcome_text = f"""
🏰 **مرحباً بك في إمبراطورية المعرفة، {user.first_name}!** 🎓

أنت الآن في نظام تعليمي ذكي يتكيف مع أدائك ويتحدى قدراتك.

✨ **مميزات النظام الجديدة:**
✅ نظام بطاقات سلوك (🟡🟢🔴)
✅ مكافحة غش ذكية متدرجة
✅ أسئلة مقاومة للنسخ
✅ تحديات شخصية ذكية

🚀 **ابدأ رحلتك الآن:**"""
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_cards_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض بطاقات المستخدم"""
        user_id = update.effective_user.id
        
        cards_display = await self.behavior_system.get_user_cards_display(user_id)
        
        # إضافة أزرار الإدارة
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_cards")],
            [InlineKeyboardButton("📈 تحسين السلوك", callback_data="improve_behavior")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
        ]
        
        await update.message.reply_text(
            f"📋 **سجل بطاقات السلوك**\n\n{cards_display}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def smart_challenge_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء تحدي ذكي مقاوم للغش"""
        user_id = update.effective_user.id
        
        # تحديد مستوى مقاومة الغش بناءً على سجل المستخدم
        cheat_level = await self._get_user_cheat_level(user_id)
        anti_cheat_level = min(5, max(1, cheat_level // 20))  # 1-5
        
        # توليد سؤال ذكي
        if self.question_gen:
            question = await self.question_gen.generate_smart_question(
                user_id=user_id,
                subject="رياضيات",  # يمكن جعله اختياراً
                difficulty="متوسط",
                anti_cheat_level=anti_cheat_level
            )
            
            # عرض السؤال مع معلومات مقاومة الغش
            challenge_text = f"""
⚔️ **تحدي ذكي مقاوم للغش** ⚔️

🛡️ **مستوى الحماية:** {anti_cheat_level}/5
🎯 **الصعوبة:** {question.get('difficulty', 'متوسط')}
⏱️ **الوقت:** {question.get('time', 60)} ثانية
🏆 **النقاط:** {question.get('points', 50)}

❓ **السؤال:**
{question.get('question_text', '')}

📝 **الخيارات:**
"""
            # عرض الخيارات
            options = question.get('options', {})
            for letter, text in options.items():
                challenge_text += f"{letter}) {text}\n"
            
            challenge_text += f"\n🔍 **ميزات مقاومة الغش:** {', '.join(question.get('rules_applied', []))}"
            
            # حفظ السؤال في الجلسة
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id]['current_question'] = question
            
            keyboard = [
                [InlineKeyboardButton("أ", callback_data="answer_a"),
                 InlineKeyboardButton("ب", callback_data="answer_b"),
                 InlineKeyboardButton("ج", callback_data="answer_c"),
                 InlineKeyboardButton("د", callback_data="answer_d")],
                [InlineKeyboardButton("⏰ تمديد الوقت", callback_data="extend_time"),
                 InlineKeyboardButton("🏃 هرب", callback_data="give_up")]
            ]
            
            await update.message.reply_text(
                challenge_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأزرار"""
        query = update.callback_query
        await query.answer()
        
        handlers = {
            "smart_challenges": self.show_smart_challenges_menu,
            "behavior_profile": self.show_behavior_profile,
            "my_cards": self.show_my_cards,
            "home": self.show_main_menu,
            # ... إضافة المزيد من المعالجات
        }
        
        handler = handlers.get(query.data)
        if handler:
            await handler(update, context)
    
    async def show_behavior_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض ملف السلوك"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # جلب بيانات السلوك
        async with aiosqlite.connect("empire_pro.db") as db:
            cursor = await db.execute(
                "SELECT behavior_score, cheat_level FROM users WHERE id = ?",
                (user_id,)
            )
            user_data = await cursor.fetchone()
        
        if user_data:
            behavior_score = user_data[0]
            cheat_level = user_data[1]
            
            # تحليل السلوك
            behavior_analysis = self._analyze_behavior_score(behavior_score)
            
            # إنشاء تقرير بصري
            report = f"""
📊 **تقرير السلوك التفصيلي**

⭐ **نقاط السلوك:** {behavior_score}/100
{self._create_behavior_bar(behavior_score)}

🛡️ **مستوى الغش:** {cheat_level}/100
{self.anti_cheat._create_visual_indicator(cheat_level)}

📈 **التقييم:** {behavior_analysis['rating']}
💡 **التوصية:** {behavior_analysis['recommendation']}

🎯 **الأهداف القادمة:**
{behavior_analysis['goals']}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث", callback_data="behavior_profile")],
                [InlineKeyboardButton("📋 بطاقاتي", callback_data="my_cards")],
                [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
            ]
            
            await query.edit_message_text(
                report,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
    
    def _create_behavior_bar(self, score: int) -> str:
        """إنشاء شريط تقدم بصري للسلوك"""
        filled = int(score / 5)  # 20 مستطيلات
        empty = 20 - filled
        
        bar = "▰" * filled + "▱" * empty
        return f"`[{bar}]`"
    
    def _analyze_behavior_score(self, score: int) -> Dict:
        """تحليل نقاط السلوك"""
        if score >= 90:
            return {
                'rating': "🌟 ممتاز",
                'recommendation': "استمر في هذا الأداء الرائع!",
                'goals': "- الحفاظ على 90+ نقطة\n- مساعدة الآخرين\n- قيادة التحديات"
            }
        elif score >= 70:
            return {
                'rating': "👍 جيد جداً",
                'recommendation': "أنت على الطريق الصحيح!",
                'goals': "- الوصول لـ 80 نقطة\n- تحسين التفاعل\n- خفض البطاقات الصفراء"
            }
        elif score >= 50:
            return {
                'rating': "⚠️ يحتاج تحسين",
                'recommendation': "ركز أكثر على الجودة بدل السرعة",
                'goals': "- تجنب البطاقات الصفراء\n- تحسين الدقة\n- زيادة المشاركة"
            }
        else:
            return {
                'rating': "🔴 يحتاج اهتمام",
                'recommendation': "راجع قواعد النظام وحاول التحسن",
                'goals': "- عدم الحصول على بطاقات\n- طلب المساعدة\n- التركيز على التعلم"
            }
    
    async def _get_user_cheat_level(self, user_id: int) -> int:
        """الحصول على مستوى غش المستخدم"""
        if user_id in self.anti_cheat.cheat_scores:
            return self.anti_cheat.cheat_scores[user_id]
        
        async with aiosqlite.connect("empire_pro.db") as db:
            cursor = await db.execute(
                "SELECT cheat_level FROM users WHERE id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0

# ==================== تشغيل البوت ====================
async def main():
    """الدالة الرئيسية لتشغيل البوت"""
    bot = HamzaEmpireProBot()
    await bot.init_bot()
    
    # تشغيل البوت
    await bot.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # ملف requirements.txt المطلوب:
    """
    python-telegram-bot[job-queue]==20.7
    groq==0.6.0
    aiosqlite==0.19.0
    python-dotenv==1.0.0
    """
    
    # ملف .env المطلوب:
    """
    BOT_TOKEN=توكن_البوت_الحقيقي
    GROQ_API_KEY=مفتاح_groq_الحقيقي
    """
    
    asyncio.run(main())
