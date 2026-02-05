import asyncio
import os
import re
import shutil
from pyrogram import Client, filters, errors

# --- الربط الذكي مع مدخلات Render ---
# نستخدم get() مع قيمة افتراضية لتجنب التعارض أو الانهيار
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# فحص سريع للمدخلات في السجلات (Logs) للتأكد من القراءة
if not all([API_ID, API_HASH, BOT_TOKEN, STRING_SESSION]):
    print("⚠️ تنبيه: أحد مدخلات Render مفقود! تأكد من ملء Environment Variables.")

app = Client(
    "Hamza_Pro_Safe",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    session_string=STRING_SESSION,
    workers=50 # توازن مثالي للسرعة على Render
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
    await message.reply_text(
        "🦁 **القناص حمزة PRO - النسخة الآمنة**\n\n"
        "✅ البوت متصل الآن بمنصة Render بنجاح.\n"
        "✅ نظام التنظيف التلقائي للمساحة: **مفعل**.\n\n"
        "أرسل الأمر كالتالي:\n"
        "`/get video 10 [الرابط]`"
    )

@app.on_message(filters.command("get") & filters.private)
async def bulk_get(client, message):
    folder = f"temp_{message.from_user.id}"
    try:
        args = message.text.split()
        if len(args) < 4: return await message.reply("⚠️ الصيغة: `/get [النوع] [العدد] [الرابط]`")

        f_type, count, link = args[1].lower(), int(args[2]), args[3]
        data = get_chat_info(link)
        if not data: return await message.reply("❌ الرابط غير صحيح")

        chat_id, start_id = data
        os.makedirs(folder, exist_ok=True)
        status = await message.reply("⏳ **جاري الجلب والرفع (بترتيب الدورة)...**")
        
        success = 0
        for i in range(count):
            try:
                msg_id = start_id + i
                msg = await client.get_messages(chat_id, msg_id)
                if not msg or msg.empty: continue

                # نظام فلترة الميديا
                should_download = (f_type == "all") or \
                                  (f_type == "video" and msg.video) or \
                                  (f_type == "document" and msg.document) or \
                                  (f_type == "photo" and msg.photo)

                if should_download:
                    # التحميل محلياً للترتيب وتخطي منع التوجيه
                    file_path = await msg.download(file_name=f"{folder}/{success+1:03d}_")
                    
                    # الرفع للمستخدم
                    await message.reply_document(file_path, caption=f"📁 الملف: {success+1}")
                    
                    # 🗑️ الحذف الفوري من سيرفر Render لمنع امتلاء التخزين
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    success += 1
                    await asyncio.sleep(1.5) # فاصل زمني لتجنب حظر تليجرام

            except errors.FloodWait as e:
                await asyncio.sleep(e.value + 5)
            except Exception: continue

        await status.edit(f"✅ **تم قنص {success} ملف بنجاح!**\nوتم تنظيف مساحة السيرفر.")

    except Exception as e:
        await message.reply(f"❌ خطأ: `{str(e)}`")
    finally:
        # تأكيد
