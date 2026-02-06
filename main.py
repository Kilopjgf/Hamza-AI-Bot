import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- إبقاء Render نشط ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Transfer Engine: ONLINE")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- بيانات الدخول ---
API_ID = 32630729
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='


client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def transfer_message(target, msg):
    """نقل الرسائل مع التفريق بين النصوص والوسائط"""
    try:
        if msg.text and len(msg.text) > 10:
            await client.send_message(target, msg.text)
        elif msg.media:
            await client.send_file(
                target,
                msg.media,
                caption=msg.text or "",
                force_document=False,
                supports_streaming=True
            )
        print(f"✅ تم نقل الرسالة {msg.id}")
        return True
    except errors.FloodWaitError as e:
        print(f"⚠️ FloodWait: انتظار {e.seconds} ثانية")
        await asyncio.sleep(e.seconds)
        return await transfer_message(target, msg)
    except Exception as e:
        print(f"❌ خطأ في الرسالة {msg.id}: {e}")
        return False

async def main():
    source = '@bac_2026_koki'  # القناة المصدر
    target = 'https://t.me/+EI4JWuPnp3M4MjA0'  # القناة الهدف

    await client.start()
    source_entity = await client.get_entity(source)
    target_entity = await client.get_entity(target)

    print("📦 جاري جلب الرسائل...")
    messages = await client.get_messages(source_entity, limit=4000, reverse=True)

    for i, msg in enumerate(messages, start=1):
        success = await transfer_message(target_entity, msg)
        if success:
            print(f"🚀 تقدم: {i}/{len(messages)}")
        # تأخير ذكي: أقل للنصوص، أكثر للفيديوهات
        await asyncio.sleep(1 if msg.text else 5)

    print("🏁 اكتمل النقل بنجاح!")

if __name__ == '__main__':
    threading.Thread(target=run_mock_server, daemon=True).start()
    with client:
        client.loop.run_until_complete(main())
