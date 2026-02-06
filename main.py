from telethon import TelegramClient
from telethon.sessions import StringSession # أضفنا هذا السطر
import asyncio

# بياناتك الحقيقية
api_id = 32630729 
api_hash = 'edf5520c08c8df7b3408acbda46f3140'
# ضع هنا الكود الطويل الذي حصلت عليه من Google Colab
string_session = '1BV...ضع_الكود_هنا...' 

# التعديل الجوهري: نستخدم StringSession بدلاً من اسم ملف
client = TelegramClient(StringSession(string_session), api_id, api_hash)

async def main():
    source_channel = 'bac_2026_koki'
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'
    
    print("🚀 البدء باستخدام الجلسة المحفوظة...")
    async for msg in client.iter_messages(source_channel, limit=4000, reverse=True):
        try:
            await client.send_message(target_channel, msg)
            await asyncio.sleep(2)
            print(f"✅ تم نقل رسالة بنجاح")
        except Exception as e:
            print(f"❌ خطأ: {e}")

with client:
    client.loop.run_until_complete(main())
