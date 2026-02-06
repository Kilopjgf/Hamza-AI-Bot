from telethon import TelegramClient
import asyncio
import os

# بياناتك الحقيقية
api_id = 32630729
api_hash = 'edf5520c08c8df7b3408acbda46f3140'

# استخدام اسم جلسة ثابت لتجنب تسجيل الدخول المتكرر
client = TelegramClient('session_bac_codex', api_id, api_hash)

async def main():
    # المصدر: القناة التي تريد السحب منها
    source_channel = 'bac_2026_koki' 
    # الهدف: مجموعتك أو قناتك الخاصة
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'

    print("🚀 جاري بدء عملية النقل... انتظر قليلاً.")
    
    count = 0
    # iter_messages سيتجاوز الحماية لأنك مسجل كـ "مستخدم"
    async for msg in client.iter_messages(source_channel, limit=4000, reverse=True):
        try:
            count += 1
            # نقل الرسائل النصية والوسائط
            await client.send_message(target_channel, msg)
            
            # تأخير زمني لتجنب حظر تلجرام (Flood Wait)
            await asyncio.sleep(2) 
            print(f"✅ تم نقل المنشور رقم: {count}")
            
        except Exception as e:
            print(f"❌ خطأ في نقل الرسالة {count}: {e}")
            continue

    print(f"🎉 انتهى النقل بنجاح! إجمالي المنشورات: {count}")

with client:
    client.loop.run_until_complete(main())
