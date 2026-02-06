import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ إبقاء الخدمة حية في Render ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running...")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ إعدادات تليجرام ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def main():
    source = 'bac_2026_koki'
    target = 'https://t.me/+EI4JWuPnp3M4MjA0'

    await client.start()
    print("🚀 تم الاتصال. بدء التحويل المباشر القسري الآن...")

    # جلب الكيانات لضمان عدم حدوث خطأ في الوصول
    try:
        source_entity = await client.get_entity(source)
        target_entity = await client.get_entity(target)
    except Exception as e:
        print(f"❌ خطأ في الوصول للقنوات: {e}")
        return

    count = 0
    # استخدام iter_messages مع reverse=True لنقل الدروس بالترتيب
    async for msg in client.iter_messages(source_entity, reverse=True):
        try:
            # الخدعة البرمجية: إرسال الرسالة كـ 'نسخة' تتجاوز منع التحويل
            await client.send_message(target_entity, msg)
            count += 1
            print(f"✅ تم نقل المنشور رقم {count} (ID: {msg.id})")
            
            # انتظار بسيط جداً لضمان السرعة مع تجنب الحظر
            await asyncio.sleep(2) 
            
        except Exception as e:
            print(f"⚠️ تخطي منشور {msg.id} بسبب: {e}")
            continue

    print(f"🏁 اكتملت المهمة! تم نقل {count} منشور بنجاح.")

if __name__ == '__main__':
    threading.Thread(target=run_mock_server, daemon=True).start()
    with client:
        client.loop.run_until_complete(main())
