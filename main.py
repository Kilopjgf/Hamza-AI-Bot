import asyncio
import os
import re
from pyrogram import Client, filters, errors
from pyrogram.types import Message

# --- إعدادات البيئة (Render Environment Variables) ---
API_ID = int(os.environ.get("API_ID", 34118961))
API_HASH = os.environ.get("API_HASH", "0b53e526ea59d87bd0236eed5338abe5")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
STRING_SESSION = os.environ.get("STRING_SESSION")

# إعداد العميل بأعلى كفاءة
app = Client(
    "Hmza_Ultra_Bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    session_string=STRING_SESSION,
    workers=50,             # سرعة معالجة قصوى
    sleep_threshold=120     # تخطي فترات الانتظار الطويلة تلقائياً
)

def get_chat_info(link):
    """تحليل ذكي لروابط تليجرام"""
    pattern = r"t\.me/(?:c/)?([^/]+)/(\d+)"
    match = re.search(pattern, link)
    if not match: return None
    chat, msg_id = match.group(1), int(match.group(2))
    if chat.isdigit(): chat = int(f"-100{chat}")
    return chat, msg_id

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text(
        "⚡ **أهلاً بك في بوت الجلب العملاق!**\n\n"
        "لجلب محتوى مقيد بشكل متعدد، أرسل الأمر كالتالي:\n"
        "`/bulk [الرابط] [العدد]`\n\n"
        "مثال:\n`/bulk https://t.me/c/12345/10 5`"
    )

@app.on_message(filters.command("bulk") & filters.private)
async def bulk_grab(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return await message.reply("⚠️ الاستخدام الصحيح: `/bulk [الرابط] [العدد]`")

        link, count = args[1], int(args[2])
        data = get_chat_info(link)
        if not data: return await message.reply("❌ رابط غير مدعوم!")

        chat_id, start_id = data
        status = await message.reply("🚀 **جاري بدء عملية الجلب الخارقة...**")
        
        success = 0
        for i in range(count):
            curr_id = start_id + i
            try:
                # ميزة copy_message هي الأقوى لتخطي قيود المحتوى
                await client.copy_message(message.chat.id, chat_id, curr_id)
                success += 1
                if success % 5 == 0: # تحديث الحالة كل 5 رسائل للسرعة
                    await status.edit(f"📥 تم جلب `{success}` من أصل `{count}`...")
                await asyncio.sleep(0.8) # فاصل زمني مثالي لتجنب الحظر
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception: continue

        await status.edit(f"✅ **اكتملت المهمة بنجاح!**\nتم جلب `{success}` ملف/رسالة.")
    except Exception as e:
        await message.reply(f"❌ خطأ: `{str(e)}`")

print("🔥 البوت يعمل الآن بأقصى طاقة على Render!")
app.run()


