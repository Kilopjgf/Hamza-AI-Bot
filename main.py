from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import logging

# إعداد السجلات (Logs) لمراقبة النقل بدقة في منصة Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- [ إعدادات البيانات الحقيقية الخاصة بك ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
# انسخ كود الجلسة (الذي يبدأ برقم 1) وضعه بين علامتي الاقتباس بالأسفل
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='


# --- [ إعداد العميل ] ---
# استخدام .strip() ضروري جداً لحل مشكلة "ASCII characters" التي ظهرت في صورتك الأخيرة
client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def start_transfer():
    # معرف القناة المصدر والهدف
    source_channel = 'bac_2026_koki' 
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'

    try:
        print("🚀 بدأت العملية.. يتم الآن فحص الاتصال بالقنوات.")
        await client.connect()
        
        count = 0
        # reverse=True لضمان نقل الدروس بالترتيب الصحيح (من القديم للجديد)
        async for msg in client.iter_messages(source_channel, limit=4000, reverse=True):
            try:
                # نقل المنشور (نصوص، صور، ملفات) مباشرة
                await client.send_message(target_channel, msg)
                count += 1
                
                # تأخير 2 ثانية لتجنب حظر تلجرام (FloodWait) وضمان استقرار Render
                await asyncio.sleep(2) 
                if count % 10 == 0:
                    print(f"✅ تم نقل {count} منشور بنجاح حتى الآن.")
                    
            except Exception as e:
                logger.error(f"⚠️ خطأ في
