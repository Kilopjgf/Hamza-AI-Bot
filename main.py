import os
import time
import random
import logging
import asyncio
import aiosqlite
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")      # من Render
GROUP_ID = int(os.getenv("GROUP_ID"))   # ID القروب
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # اختياري

DB_FILE = "bacmaster.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BacMaster")

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            trust REAL DEFAULT 1.0,
            last_answer REAL DEFAULT 0
        )
        """)
        await db.commit()

# ================= AI QUESTION ENGINE =================
def generate_question():
    subjects = [
        ("رياضيات", "ما نهاية المتتالية 2n + 1 عندما n→∞ ؟"),
        ("علوم", "ما دور الأنزيم في التفاعل الحيوي؟"),
        ("تاريخ", "ما مفهوم التعايش السلمي في الحرب الباردة؟"),
        ("فرنسية", "ما هدف بيان أول نوفمبر 1954؟"),
        ("English", "What does 'as long as' express?")
    ]
    subject, q = random.choice(subjects)
    return f"🧠 *سؤال {subject}*\n\n{q}"

CORRECT_KEYWORDS = {
    "رياضيات": ["لانهاية", "∞"],
    "علوم": ["تسريع", "محفز"],
    "تاريخ": ["تجنب الحرب", "سلمي"],
    "فرنسية": ["الاستقلال"],
    "English": ["condition", "while"]
}

# ================= ANTI CHEAT =================
async def update_user(db, user_id, delta_points, speed):
    async with db.execute("SELECT points, level, trust FROM users WHERE user_id=?",
                          (user_id,)) as cursor:
        row = await cursor.fetchone()

    if row is None:
        points, level, trust = 0, 1, 1.0
        await db.execute("INSERT INTO users(user_id) VALUES(?)", (user_id,))
    else:
        points, level, trust = row

    # Anti-Cheat Logic
    if speed < 2:
        trust -= 0.1
        delta_points = max(0, delta_points - 1)
    else:
        trust = min(1.0, trust + 0.02)

    points += delta_points
    if points >= level * 10:
        level += 1

    await db.execute("""
        UPDATE users
        SET points=?, level=?, trust=?, last_answer=?
        WHERE user_id=?
    """, (points, level, trust, time.time(), user_id))

# ================= HANDLER =================
last_question_time = 0
current_subject = None

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_question_time, current_subject

    if update.effective_chat.id != GROUP_ID:
        return

    text = update.message.text.lower()
    user_id = update.effective_user.id

    async with aiosqlite.connect(DB_FILE) as db:

        # ===== Trigger question =====
        if "سؤال" in text or "لغز" in text:
            q = generate_question()
            current_subject = q.split("*")[1].replace("سؤال", "").strip()
            last_question_time = time.time()
            await update.message.reply_text(q, parse_mode="Markdown")
            return

        # ===== Answer detection =====
        if current_subject:
            speed = time.time() - last_question_time
            keywords = CORRECT_KEYWORDS.get(current_subject, [])

            if any(k in text for k in keywords):
                await update_user(db, user_id, delta_points=3, speed=speed)
                await db.commit()
                await update.message.reply_text("🎉 إجابة صحيحة! +3 نقاط")
                current_subject = None
            else:
                await update.message.reply_text("❌ حاول مرة أخرى")

# ================= MAIN =================
async def main():
    await init_db()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🚀 BacMaster Super Empire Mode يعمل الآن")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

