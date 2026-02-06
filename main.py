import asyncio
from telethon import TelegramClient, errors, types
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ إبقاء الخدمة حية على Render ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Advanced Smart-Transfer: RUNNING")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ الإعدادات ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH, sequential_updates=False)

# ضع هنا معرف الـ Topic الخاص بالدردشة لاستثنائه (يمكنك معرفته من سجلات البوت)
CHAT_TOPIC_ID = None 

async def transfer_logic(target, msg):
    """منطق النقل الذكي للميديا والملفات"""
    try:
        # 1. تصفية رسائل الدردشة (الرسائل التي ليس لها ميديا وغالباً تكون قصيرة)
        if not msg.media and len(msg.text or "") < 5:
            return

        # 2. نقل الميديا الثقيلة (فيديوهات، ملفات، صور)
        if msg.media:
            # استخدام خاصية الرفع المباشر لكسر الحماية وتجاوز المنع
            await client.send_file(target, msg.media, caption=msg.text, force_document=False)
        else:
            await client.send_message(target, msg.text)
        return True
    except errors.FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return await transfer_logic(target, msg)
    except Exception as e:
        print(f"❌ خطأ في نقل المنشور {msg.id}: {e}")
        return False

async def main():
    source = 'bac_2026_koki'
    target = 'https://t.me/+EI4JWuPnp3M4MjA0'

    await client.start()
    print("🚀 انطلاق محرك النقل الذكي الشامل...")

    source_entity = await client.get_entity(source)
    target_entity = await client.get_entity(target)

    count = 0
    # جلب الرسائل بالترتيب (من الأقدم للأحدث لضمان ترتيب الدروس)
    async for msg in client.iter_messages(source_entity, reverse=True):
        # تخطي المواضيع المخصصة للدردشة إذا كان لها ID معروف
        if hasattr(msg, 'reply_to') and msg.reply_to and msg.reply_to.reply_to_msg_id == CHAT_TOPIC_ID:
            continue
            
        success = await transfer_logic(target_entity, msg)
        if success:
            count += 1
            if count % 5 == 0:
                print(f"⚡ تم نقل {count} منشور (بما في ذلك ملفات وفيديوهات)")
        
        # فاصل زمني بسيط للسماح لـ Render بمعالجة الملفات الكبيرة
        await asyncio.sleep(1.5)

if __name__ == '__main__':
    threading.Thread(target=run_mock_server, daemon=True).start()
    with client:
        client.loop.run_until_complete(main())
