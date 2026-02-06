from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)

# --- [ بياناتك الحقيقية ] ---
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def start_transfer():
    # استخدام المعرف الرقمي للقناة المصدر لتفادي فحص الرابط المتكرر
    source_channel = 'bac_2026_koki' 
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'

    try:
        await client.start()
        print("🚀 الاتصال ناجح. جاري كسر حماية منع التحويل...")
        
        # الحصول على القناة كمادة (Entity) مرة واحدة فقط لتقليل الطلبات
        source_entity = await client.get_entity(source_channel)
        
        count = 0
        async for msg in client.iter_messages(source_entity, limit=4000, reverse=True):
            try:
                # التحقق إذا كان المنشور يحتوي على ميديا (صورة، فيديو، ملف)
                if msg.media:
                    # تحميل الميديا في الذاكرة وإعادة رفعها لتجاوز حماية منع التحويل
                    await client.send_file(target_channel, msg.media, caption=msg.text)
                elif msg.text:
                    # إرسال النص كرسالة جديدة
                    await client.send_message(target_channel, msg.text)
                
                count += 1
                # فاصل زمني "ذكي" (7 ثوانٍ) لتجنب FloodWait تماماً
                await asyncio.sleep(7) 
                
                if count % 5 == 0:
                    print(f"✅ تم نقل {count} منشور (بكسر الحماية).")
                    
            except FloodWaitError as e:
                print(f"⚠️ حظر مؤقت! يجب الانتظار {e.seconds} ثانية...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"❌ خطأ في منشور: {e}")
                continue

    except Exception as e:
        print(f"❌ خطأ عام: {e}")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(start_transfer())
