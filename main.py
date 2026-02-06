import asyncio
import os
from telethon import TelegramClient, errors, utils
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- [ نظام الحفاظ على استمرارية السيرفر ] ---
class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Genius Transfer Engine: ONLINE")

def run_mock_server():
    server = HTTPServer(('0.0.0.0', 10000), MockServer)
    server.serve_forever()

# --- [ إعدادات القوة المطلقة ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def genius_transfer(target, msg):
    """خوارزمية سحب الميديا والملفات بأعلى دقة وتنظيم"""
    try:
        # إذا كان المحتوى ميديا (فيديو HD، ملفات PDF، صور)
        if msg.media:
            print(f"💎 جاري معالجة ميديا ذكية (ID: {msg.id})...")
            # السر العبقري: استخدام 'supports_streaming' لضمان عمل الفيديوهات الطويلة فوراً
            # واستخدام 'thumb' إذا توفر لضمان دقة العرض
            await client.send_file(
                target, 
                msg.media, 
                caption=msg.text, 
                force_document=False, 
                supports_streaming=True,
                progress_callback=lambda d, t: print(f"📊 جاري الرفع: {d/t:.1%}") if t > 0 else None
            )
            return True
        
        # نقل النصوص الطويلة والدروس المكتوبة بدقة
        elif msg.text and len(msg.text) > 10:
            await client.send_message(target, msg.text)
            return True
            
    except errors.Flood
    
