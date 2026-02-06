from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import logging

# إعداد السجلات (Logs) لمراقبة النقل بدقة في منصة Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- [ إعدادات البيانات الحقيقية ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
# كود الجلسة الخاص بك الذي وضعته في رسالتك
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

# --- [ إعداد العميل ] ---
# استخدام .strip() ضروري جداً لحل مشكلة "ASCII characters"
client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def start_transfer():
    # معرف القناة المصدر والهدف
    source_channel = 'bac_2026_koki' 
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'

    try:
        print("🚀 بدأت العملية.. يتم الآن فحص الاتصال بالقنوات.")
        await client.start()
        
        count = 0
        # السحب بالترتيب الصحيح (من القديم للجديد)
        async for msg in client.iter_messages(source_channel, limit=4000, reverse=True):
            try:
                # نقل المنشور بالكامل
                await client.send_message(target_channel, msg)
                count += 1
                
                # تأخير 2 ثانية لتجنب الحظر
                await asyncio.sleep(2) 
                if count % 10 == 0:
                    print(f"✅ تم نقل {count} منشور بنجاح حتى الآن.")
                    
            except Exception as e:
                # هذا هو السطر الذي كان يسبب SyntaxError، تم تصحيحه الآن
                logger.error(f"⚠️ خطأ في المنشور رقم {count}: {e}")
                continue

        print(f"🎉 تم الانتهاء! إجمالي ما تم نقله: {count} منشور.")

    except Exception as e:
        logger.error(f"❌ خطأ كارثي في الاتصال: {e}")

# تشغيل السكريبت
if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(start_transfer())
