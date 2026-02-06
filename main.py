import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ إعداد منفذ وهمي لإرضاء منصة Render ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running...")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ بياناتك الحقيقية ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def start_transfer():
    source_channel = 'bac_2026_koki' 
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'

    await client.start()
    print("🚀 تم الاتصال بنجاح. كسر الحماية بدأ الآن...")
    
    source_entity = await client.get_entity(source_channel)
    count = 0
    async for msg in client.iter_messages(source_entity, limit=4000, reverse=True):
        try:
            # تحميل وإعادة رفع لتجاوز "منع التحويل"
            if msg.media:
                await client.send_file(target_channel, msg.media, caption=msg.text)
            elif msg.text:
                await client.send_message(target_channel, msg.text)
            
            count += 1
            await asyncio.sleep(10) # انتظار آمن
            if count % 5 == 0:
                print(f"✅ تم نقل {count} منشور.")
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception:
            continue

if __name__ == '__main__':
    # تشغيل المنفذ الوهمي في خيط منفصل لمنع إغلاق الخدمة
    threading.Thread(target=run_mock_server, daemon=True).start()
    with client:
        client.loop.run_until_complete(start_transfer())
