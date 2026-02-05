import asyncio
import os
import re
from pyrogram import Client, filters, errors

# --- الإعدادات ---
API_ID = int(os.environ.get("API_ID", 34118961))
API_HASH = os.environ.get("API_HASH", "0b53e526ea59d87bd0236eed5338abe5")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
STRING_SESSION = os.environ.get("STRING_SESSION")

# تشغيل البوت بأعلى صلاحيات الحساب الشخصي
app = Client(
    "Hamza_Pro_Grabber",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    session_string=STRING_SESSION,
    workers=20
)

def get_chat_info(link):
    pattern = r"t\.me/(?:c/)?([^/]+)/(\d+)"
    match = re.search(pattern, link)
    if not match: return None
    chat, msg_id = match.group(1), int(match.group(2))
    if chat.isdigit(): chat = int(f"-100{chat}")
    return chat, msg_id

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("🦁 **مرحباً بك يا حمزة!**\nأرسل الأمر هكذا: `/bulk [الرابط] [العدد]`")

@app.on_message(filters.command("bulk") & filters.private)
async def bulk_grab(client, message):
    try:
        args = message.text.split()
        if len(args) < 3: return
        
        link, count = args[1], int(args[2])
        data = get_chat_info(link)
        if not data: return
        
        chat_id, start_id = data
        status = await message.reply("⏳ **جاري اختراق الحماية وجلب الملفات...**")
        
        success = 0
        for i in range(count):
            try:
                msg_id = start_id + i
                # جلب الرسالة الأصلية
                msg = await client.get_messages(chat_id, msg_id)
                
                # إرسالها كرسالة جديدة تماماً لتخطي منع التوجيه
                if msg.media:
                    await msg.copy(message.chat.id, caption=msg.caption)
                elif msg.text:
                    await client.send_message(message.chat.id, msg.text)
                
                success += 1
                await asyncio.sleep(1.5) # فاصل زمني لتجنب حظر تليجرام
            except Exception: continue

        await status.edit(f"✅ **اكتمل القنص بنجاح!**\nتم جلب `{success}` ملف/رسالة.")
    except Exception as e:
        await message.reply(f"❌ خطأ: `{str(e)}`")

app.run()


