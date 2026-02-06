import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ إرضاء منصة Render لضمان عدم التوقف ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hyper Speed Transfer Active")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ إعدادات القوة والبيانات ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
# الـ String Session الخاص بك (تمت إضافة .strip لتجنب خطأ ASCII)
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH, sequential_updates=False)

async def worker(queue, target_entity):
    """عامل خاص يقوم بسحب المهام من الطابور وتنفيذها فوراً"""
    while True:
        msg = await queue.get()
        try:
            # النقل المباشر لسرعة أكبر
            await client.send_message(target_entity, msg)
            print(f"🚀 تم ضخ المنشور {msg.id}")
        except errors.FloodWaitError as e:
            print(f"⚠️ حماية تلجرام: انتظار {e.seconds} ثانية")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ خطأ بسيط: {e}")
        finally:
            queue.task_done()
            await asyncio.sleep(0.1) # فاصل زمني مجهري للسرعة

async def main():
    source = 'bac_2026_koki'
    target = 'https://t.me/+EI4JWuPnp3M4MjA0'

    await client.start()
    source_entity = await client.get_entity(source)
    target_entity = await client.get_entity(target)

    # إنشاء طابور مهام (Queue) لضمان القوة
    queue = asyncio.Queue()
    
    # جلب جميع الرسائل دفعة واحدة (4000 منشور)
    print("📦 جاري جلب قاعدة البيانات بالكامل...")
    messages = await client.get_messages(source_entity, limit=4000, reverse=True)
    
    for m in messages:
        await queue.put(m)

    # تشغيل 10 عمال (Workers) في نفس الوقت لسرعة خارقة
    tasks = []
    for _ in range(10):
        task = asyncio.create_task(worker(queue, target_entity))
        tasks.append(task)

    print(f"🔥 انطلاق 10 محركات للنقل المتوازي لـ {len(messages)} منشور...")
    await queue.join() # الانتظار حتى انتهاء كل المهام

    for task in tasks:
        task.cancel()
    print("🏁 اكتمل النقل الشامل بنجاح باهر!")

if __name__ == '__main__':
    threading.Thread(target=run_mock_server, daemon=True).start()
    with client:
        client.loop.run_until_complete(main())
