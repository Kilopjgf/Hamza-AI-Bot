import asyncio
import os
import re
import shutil
from pyrogram import Client, filters, errors

# جلب الإعدادات من Render تلقائياً
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

app = Client(
    "Hamza_Pro_Ultimate",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    session_string=STRING_SESSION,
    workers=50
)

def get_chat_info(link):
    pattern = r"t\.me/(?:c/)?([^/]+)/(\d+)"
    match = re.search(pattern, link)
    if not match: return None
    chat, msg_id = match.group(1), int(match.group(2))
    if str(chat).isdigit(): chat = int(f"-100{chat}")
    return chat, msg_id

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("🦁 **أهلاً بك يا حمزة في النسخة الاحترافية!**\n\nالسحب يعمل بترتيب الدورة مع تنظيف تلقائي للمساحة.\n\nالصيغة:\n`/get video 10 [الرابط]`")

@app.on_message(filters.command("get") & filters.private)
async def bulk_get(client, message):
    folder = f"job_{message.from_user.id}"
    try:
        args = message.text.split()
        if len(args) < 4: return await message.reply("⚠️ `/get [نوع] [عدد] [رابط]`")

        f_type, count, link = args[1].lower(), int(args[2]), args[3]
        data = get_chat_info(link)
        if not data: return await message.reply("❌ رابط غير صالح")

        chat_id, start_id = data
        os.makedirs(folder, exist_ok=True)
        status = await message.reply("🚀 **بدأ القنص والترتيب...**")
        
        success = 0
        for i in range(count):
            try:
                msg_id = start_id + i
                msg = await client.get_messages(chat_id, msg_id)
                if not msg or msg.empty: continue

                # تحقق من النوع
                is_target = (f_type == "all") or \
                            (f_type == "video" and msg.video) or \
                            (f_type == "document" and msg.document)

                if is_target:
                    # تحميل وتسمية الملف بالترتيب
                    path = await msg.download(file_name=f"{folder}/{success+1:03d}_")
                    # الرفع للمستخدم
                    await message.reply_document(path, caption=f"📁 الملف: {success+1}")
                    # مسح الملف فوراً لتوفير مساحة في Render
                    if os.path.exists(path): os.remove(path)
                    success += 1
                    await asyncio.sleep(1.5)

            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 5)
            except Exception: continue

        await status.edit(f"✅ **اكتمل سحب {success} ملف بنجاح!**")
    except Exception as e:
        await message.reply(f"❌ خطأ: `{str(e)}`")
    finally:
        shutil.rmtree(folder, ignore_errors=True)

if __name__ == "__main__":
    app.run()
