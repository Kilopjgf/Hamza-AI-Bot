import asyncio
import os
import re
from pyrogram import Client, filters, errors

# --- جلب البيانات من Render (بدون تعارض) ---
# هذه الأسطر تقرأ المدخلات التي وضعتها أنت في لوحة تحكم Render تلقائياً
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# إعداد العميل (القناص حمزة)
app = Client(
    "Hamza_Pro",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    session_string=STRING_SESSION,
    workers=20
)

# دالة تحليل الروابط
def get_chat_info(link):
    pattern = r"t\.me/(?:c/)?([^/]+)/(\d+)"
    match = re.search(pattern, link)
    if not match: return None
    chat, msg_id = match.group(1), int(match.group(2))
    if str(chat).isdigit(): chat = int(f"-100{chat}")
    return chat, msg_id

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("🦁 **مرحباً بك يا حمزة في بوتك الخاص!**\n\nأرسل الأمر هكذا:\n`/bulk [الرابط] [العدد]`")

@app.on_message(filters.command("bulk") & filters.private)
async def bulk_grab(client, message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return await message.reply("⚠️ الاستخدام: `/bulk [الرابط] [العدد]`")
        
        link, count = args[1], int(args[2])
        data = get_chat_info(link)
        if not data:
            return await message.reply("❌ الرابط غير صحيح!")
        
        chat_id, start_id = data
        status = await message.reply("🚀 **بدأ القناص حمزة بجلب الميديا...**")
        
        success = 0
        for i in range(count):
            try:
                curr_id = start_id + i
                # استخدام get_messages لجلب الرسالة حتى لو كانت محمية
                msg = await client.get_messages(chat_id, curr_id)
                
                if msg and not msg.empty:
                    # نسخ الرسالة بالكامل (تتخطى الحماية)
                    await msg.copy(message.chat.id)
                    success += 1
                
                # تأخير بسيط لتجنب حظر تليجرام (Flood)
                await asyncio.sleep(1.2)
            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception:
                continue

        await status.edit(f"✅ **انتهت المهمة يا حمزة!**\nتم جلب `{success}` ملفات بنجاح.")
    except Exception as e:
        await message.reply(f"❌ حدث خطأ: `{str(e)}`")

# تشغيل البوت
if __name__ == "__main__":
    print("⚡ البوت يعمل الآن بأقصى قوة...")
    app.run()


