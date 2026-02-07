import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ نظام البقاء حيًا على Render ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Ultimate Bot Engine: ACTIVE")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ إعدادات الهوية والقوة ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def genius_transfer(target, msg):
    """المحرك العبقري لسحب المحتوى المقيد"""
    try:
        # كسر الحماية عبر إعادة الرفع الخام (تجاوز رسالة منع السحب)
        if msg.media:
            print(f"📥 سحب ميديا ثقيلة: {msg.id}")
            await client.send_file(
                target, 
                msg.media, 
                caption=msg.text, 
                supports_streaming=True, # للفيديوهات الطويلة جداً
                force_document=False
            )
        elif msg.text:
            await client.send_message(target, msg.text)
        return True
    except errors.FloodWaitError as e:
        print(f"⚠️ حماية تلجرام: انتظار {e.seconds} ثانية...")
        await asyncio.sleep(e.seconds)
        return await genius_transfer(target, msg)
    except Exception as e:
        print(f"❌ خطأ في نقل المنشور {msg.id}: {e}")
        return False

async def main():
    # المصدر: القناة التي تريد سحبها | الهدف: قناتك الخاصة
    source_channel = 'bac_2026_koki' 
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'

    await client.start()
    print("🔥 البوت الجاهز انطلق.. جاري كسر القيود الآن...")

    source_entity = await client.get_entity(source_channel)
    target_entity = await client.get_entity(target_channel)

    # السحب بالترتيب (من القديم للجديد) لبناء القناة بدقة
    async for msg in client.iter_messages(source_entity, reverse=True):
        # تصفية: استثناء الدردشة القصيرة جداً
        if not msg.media and (not msg.text or len(msg.text) < 10):
            continue
            
        await genius_transfer(target_entity, msg)
        
        # فاصل ذكي متكيف: 2 ثانية للملفات، 8 للفيديوهات لضمان استقرار Render
        wait_time = 8 if msg.video else 2
        await asyncio.sleep(wait_time)

if __name__ == '__main__':
    # تشغيل الخادم الوهمي في الخلفية
    threading.Thread(target=run_mock_server, daemon=True).start()
    with client:
        client.loop.run_until_complete(main())
