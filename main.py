from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

# بياناتك
api_id = 32630729
api_hash = 'edf5520c08c8df7b3408acbda46f3140'

# تأكد أن الكود داخل علامتي الاقتباس خالي من المسافات
session_string = "ضع_هنا_الكود_الذي_يبدأ_برقم_1_بدقة"

# قمنا بإضافة .strip() لإزالة أي مسافات مخفية قد تسبب خطأ ASCII
client = TelegramClient(StringSession(session_string.strip()), api_id, api_hash)

async def main():
    # المصدر والهدف
    source = 'bac_2026_koki'
    target = 'https://t.me/+EI4JWuPnp3M4MjA0'
    
    print("🚀 تم التحقق من الجلسة.. بدء النقل الآن.")
    async for msg in client.iter_messages(source, limit=4000, reverse=True):
        try:
            await client.send_message(target, msg)
            await asyncio.sleep(2) # حماية من الحظر
        except Exception as e:
            print(f"⚠️ تنبيه: {e}")

with client:
    client.loop.run_until_complete(main())
