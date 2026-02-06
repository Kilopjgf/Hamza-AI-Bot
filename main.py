
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# بياناتك الحقيقية
API_ID = 32630729 
API_HASH = 'edf5520c08c8df7b3408acbda46f3140'
STRING_SESSION = '1BJWap1sBu5WfkuQiAJZOXBFaWeBt1e6Y97UNPbsAhwaK8TvG1oJ6aKtIhfshaWnMnw5CaIlZOYnWwR2DYmyuhmsO10Tc5ddO1oMa28OuXkaZqFFeT5UlsBKvcqI4v6miacmh1RcfqB_mW7jtoJVjrHHH1q8IGXdqGB0tHffKluyxJYbAefz3RaEGvLZYmRLJpI56BpzWr3-EIxNQclUAksseyl8_Yl5iizD2Xgv8F7Vwzrbm4qXIicYrc3l2wl--YSq9EbikFGwBJYoVUQn8R1Yww_G_O74SKxpGzRezZrKudyO7EJuPeo0DE_mvfK7D6q3a9tl6hQBzbZ75VEfluqXhZjBk1D4='

client = TelegramClient(StringSession(STRING_SESSION.strip()), API_ID, API_HASH)

async def fast_transfer():
    source_channel = 'bac_2026_koki' 
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'

    try:
        await client.start()
        print("⚡ بدء التحويل السريع المباشر...")
        
        # جلب الكيان مرة واحدة للسرعة
        source_entity = await client.get_entity(source_channel)
        
        count = 0
        async for msg in client.iter_messages(source_entity, limit=4000, reverse=True):
            try:
                # التحويل المباشر للمادة دون تحميلها (أسرع بـ 10 أضعاف)
                # نستخدم send_message بدلاً من forward_messages لتجاوز قيود الحماية
                await client.send_message(target_channel, msg)
                
                count += 1
                print(f"🚀 تم تحويل المنشور {count}")
                
                # فاصل زمني قصير جداً للسرعة (ثانية واحدة)
                await asyncio.sleep(1) 
                
            except FloodWaitError as e:
                print(f"⚠️ حماية تلجرام: انتظر {e.seconds} ثانية...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"❌ تخطي منشور بسبب الحماية: {e}")
                continue

        print(f"🏁 انتهى التحويل الكلي: {count} منشور.")

    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(fast_transfer())
