import asyncio
import os
from telethon import TelegramClient, errors, types
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ إبقاء الخدمة حية لـ Render ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Educational Hurricane Engine: ACTIVE")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ إعدادات الهجوم الشامل ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH, sequential_updates=False)

async def transfer_media_and_text(target, msg):
    """المحرك المسؤول عن كسر الحماية وسحب الفيديوهات والملفات"""
    try:
        # استثناء رسائل الدردشة القصيرة جداً (أقل من 3 كلمات) التي لا تحتوي ميديا
        if not msg.media and (not msg.text or len(msg.text.split()) < 3):
            return False

        if msg.media:
            # الخدعة الكبرى: رفع الميديا كملف جديد تماماً لكسر منع الحماية
            await client.send_file(target, msg.media, caption=msg.text, force_document=False, supports_streaming=True)
        else:
            await client.send_message(target, msg.text)
        return True
    except errors.FloodWaitError as e:
        print(f"⚠️ حماية تلجرام: انتظار {e.seconds} ثانية")
        await asyncio.sleep(e.seconds)
        return await transfer_media_and_text(target, msg)
    except Exception as e:
        print(f"❌ خطأ في منشور: {e}")
        return False

async def main():
    source = 'bac_2026_koki'
    target = 'https://t.me/+EI4JWuPnp3M4MjA0'

    await client.start()
    print("🌪️ انطلاق الإعصار التعليمي.. جاري جلب الحصص والفيديوهات HD...")

    source_entity = await client.get_entity(source)
    target_entity = await client.get_entity(target)

    # سحب الرسائل بالترتيب الزمني الصحيح (من القديم للجديد) لضمان ترتيب الحصص
    count = 0
    async for msg in client.iter_messages(source_entity, reverse=True, limit=5000):
        # تنفيذ النقل
        success = await transfer_media_and_text(target_entity, msg)
        if success:
