import os
import asyncio
from pyrogram import Client, filters, errors

# --- بياناتك الشخصية التي استخرجتها ---
API_ID = 34118961
API_HASH = "0b53e526ea59d87bd0236eed5338abe5"

app = Client("BAIInTEAhAp3sQw3xBrN3AyC2Kg07dDq3vml676VOtfkLc684y0t3rvOUFc_4Wo-2a3XdfxmTQ3dNqfs0fZoCyXkZV9ezHnanzbu_uknEUswzzwrUAg9rKZ771QQtMF_GhNP-SsdONKplg5iQ970OBV9ohkjO6_hHqK-Fo4owbIiQ1gU9mXYt1prnSov1XMoVJlKpHNZk3hmEHl_P4Q9d_snOmgZD_mnGfbsFqkCzm_KRBfHS3_zM3EhW3fsuLALnrl3QW4MrAkBC24A4Ym_mzs4kYJw9Raq4crU1rhkwAEtlnuu54HQBkH1Gp2sydX6qBmNTc2DQhpR_3g1lE6P8TtGvMrqTQAAAAGqO0mxAA", api_id=API_ID, api_hash=API_HASH)

# دالة ذكية لتحليل الروابط (خاصة أو عامة)
def parse_link(link):
    if "t.me/c/" in link:
        parts = link.split('/')
        return int("-100" + parts[4]), int(parts[5])
    else:
        parts = link.split('/')
        return parts[3], int(parts[4])

# دالة السحب والرفع (بأعلى جودة وسرعة)
async def process_media(client, chat_id, msg_id):
    try:
        msg = await client.get_messages(chat_id, msg_id)
        if msg.media:
            # التحميل: يتجاوز وسم "المحتوى المقيد" تلقائياً
            file_path = await client.download_media(msg)
            # الرفع: يرسل الملف كنسخة جديدة تماماً (بدون حقوق)
            await client.send_document("me", file_path, caption=msg.caption or "✅ تم السحب بنجاح")
            # تنظيف السيرفر
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error in {msg_id}: {e}")
        return False

# 1. أمر السحب الفردي (.grab)
@app.on_message(filters.command("grab", prefixes=".") & filters.me)
async def single_grab(client, message):
    if len(message.command) < 2: return
    link = message.command[1]
    await message.edit("🔄 جاري السحب الفردي...")
    chat_id, msg_id = parse_link(link)
    if await process_media(client, chat_id, msg_id):
        await message.delete()
    else:
        await message.edit("❌ فشل السحب!")

# 2. أمر السحب الشامل (.bulk) - يسحب منشورات كثيرة في وقت واحد
@app.on_message(filters.command("bulk", prefixes=".") & filters.me)
async def bulk_grab(client, message):
    # التنسيق: .bulk [رابط_أول_منشور] [العدد]
    if len(message.command) < 3: return
    link = message.command[1]
    count = int(message.command[2])
    
    chat_id, start_id = parse_link(link)
    await message.edit(f"🚀 بدأ السحب الشامل لـ {count} منشور...")

    for i in range(count):
        current_id = start_id + i
        await process_media(client, chat_id, current_id)
        # تأخير بسيط (2 ثانية) لضمان عدم حظر الحساب من تلجرام
        await asyncio.sleep(2) 

    await message.reply("✅ اكتملت المهمة الشاملة بنجاح!")

print("⚡ البوت يعمل بنجاح! اذهب لتلجرام واستخدم .grab أو .bulk")
app.run()


