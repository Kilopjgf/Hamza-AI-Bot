import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ إرضاء Render لضمان الاستمرارية ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hyper-Transfer Engine Running...")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ إعدادات القوة ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def send_batch(target, messages):
    """إرسال دفعة كاملة من الرسائل في وقت واحد"""
    tasks = []
    for msg in messages:
        # هنا يكمن كسر الحدود: لا نطلب Forward، بل نرسل كرسالة جديدة
        tasks.append(client.send_message(target, msg))
    await asyncio.gather(*tasks)

async def main():
    source = 'bac_2026_koki' 
    target = 'https://t.me/+EI4JWuPnp3M4MjA0'

    await client.start()
    print("🚀 المحرك انطلق. جاري كسر قيود السحب...")

    source_entity = await client.get_entity(source)
    target_entity = await client.get_entity(target)

    # جلب الرسائل على دفعات (مثلاً كل 20 رسالة معاً)
    count = 0
    batch_size = 10 # حجم الدفعة لسرعة قصوى دون حظر
    
    messages_to_send = []
    async for msg in client.iter_messages(source_entity, reverse=True):
        messages_to_send.append(msg)
        
        if len(messages_to_send) >= batch_size:
            try:
                await send_batch(target_entity, messages_to_send)
                count += len(messages_to_send)
                print(f"🔥 تم ضخ دفعة: {count} منشور بنجاح.")
                messages_to_send = []
                await asyncio.sleep(2) # فاصل زمني بسيط لتجنب الـ Flood
            except errors.FloodWaitError as e:
                print(f"⚠️ تلجرام يطلب الهدوء! انتظر {e.seconds} ثانية...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"❌ خطأ في دفعة: {e}")
                messages_to_send = []

    # إرسال ما تبقى
    if messages_to_send:
        await send_batch(target_entity, messages_to_send)

if __name__ == '__main__':
    threading.Thread(target=run_mock_server, daemon=True).start()
    with client:
        client.loop.run_until_complete(main())
