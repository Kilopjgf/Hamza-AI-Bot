from telethon import TelegramClient
import asyncio

api_id = 123456          # ضع الـ api_id هنا
api_hash = 'abcdef1234567890'  # ضع الـ api_hash هنا
phone = '+213XXXXXXXXX'  # رقم الهاتف المستخدم

client = TelegramClient('render_session', api_id, api_hash)

async def main():
    source_channel = 't.me/bac_2026_koki'       # القناة المصدر (أنت عضو فيها)
    target_channel = 'https://t.me/+EI4JWuPnp3M4MjA0'  # قناتك الجديدة

    count = 0
    async for msg in client.iter_messages(source_channel, limit=4000):
        count += 1
        if msg.text:
            await client.send_message(target_channel, msg.text)
        elif msg.media:
            file = await msg.download_media()
            await client.send_file(target_channel, file)
        await asyncio.sleep(1)  # تأخير لتجنب الحظر
        print(f"✅ تم نقل {count} رسالة")

with client:
    client.start(phone)
    client.loop.run_until_complete(main())
