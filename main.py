from telethon import TelegramClient, events
import os

# المدخلات الأساسية
api_id = 34118961       # ضع الـ api_id من my.telegram.org
api_hash = '0b53e526ea59d87bd0236eed5338abe5'  # ضع الـ api_hash
phone = '+213553889762'        # رقم الهاتف للحساب المستخدم

client = TelegramClient('session_name', api_id, api_hash)

# إنشاء مجلدات للحفظ
os.makedirs("texts", exist_ok=True)
os.makedirs("photos", exist_ok=True)
os.makedirs("videos", exist_ok=True)
os.makedirs("files", exist_ok=True)

@client.on(events.NewMessage(pattern='/get'))
async def handler(event):
    channel = 't.me/bac_2026_koki'   # ضع رابط القناة هنا
    count = 0
    async for msg in client.iter_messages(channel, limit=4000):
        count += 1
        if msg.text:
            with open("texts/messages.txt", "a", encoding="utf-8") as f:
                f.write(f"{msg.id}: {msg.text}\n")
        if msg.photo:
            await msg.download_media(file="photos/")
        elif msg.video:
            await msg.download_media(file="videos/")
        elif msg.document:
            await msg.download_media(file="files/")
    await event.reply(f"✅ تم سحب {count} رسالة كاملة (نصوص + صور + فيديوهات + ملفات)")

@client.on(events.NewMessage(pattern='/cancel'))
async def cancel(event):
    await event.reply("🚫 تم إلغاء السحب")

client.start(phone)
client.run_until_disconnected()
