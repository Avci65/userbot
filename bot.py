import os
from telethon import TelegramClient, events

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

if not API_ID or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(
    session=SESSION_STRING,
    api_id=API_ID,
    api_hash=API_HASH
)

@client.on(events.NewMessage(pattern=r"\.ping"))
async def ping(event):
    await event.reply("pong ✅ (Railway)")

@client.on(events.NewMessage(pattern=r"\.id"))
async def myid(event):
    me = await client.get_me()
    await event.reply(f"ID: {me.id}")

async def main():
    me = await client.get_me()
    print(f"Userbot aktif ✅  Kullanıcı: @{me.username} | ID: {me.id}")

client.start()
client.loop.run_until_complete(main())
client.run_until_disconnected()
