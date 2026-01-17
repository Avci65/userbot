import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv("1838931", "0"))
API_HASH = os.getenv("d8ed731e06dff557170f3b6a85640522", "")
SESSION_STRING = os.getenv("1BJWap1wBu0Irb95XzQhfEyoQhIGT6PSRLwBF0jGK-DxG-RLKQVxh4juUSWv_n6_GdUycUB9fpN6iOXYl9G8xeoPGr5uS3BRQxEaZh4NknIS-aW3jw0I3JkC3lDb-ReFdr3uzvKpOAJsYLPaVNB866AwgB9TGyyif3KXjDlqNk20b6VsIOhDCs6PXsJudS8qoUXl11Xzv0NkdSKBble9oIVF5a-DM0OftlNIOG-YvM_lxiLh98-PAnj6Ie56EhrmZ4Kgor_B0oZ85Y3aH2axW_32pXbyTTZ0b5hwPnPpYE8c7GBRynMpqPeNBcRRofBqBp-NhualEr3STVDbO8vu0FWy_Su9OUms=", "")


if not API_ID or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)

@client.on(events.NewMessage(pattern=r"\.ping"))
async def ping(event):
    await event.reply("pong ✅ (Railway Userbot)")

@client.on(events.NewMessage(pattern=r"\.alive"))
async def alive(event):
    me = await client.get_me()
    await event.reply(f"✅ Çalışıyorum!\n@{me.username} | ID: {me.id}")

async def main():
    me = await client.get_me()
    print(f"Userbot başladı ✅ @{me.username} ({me.id})")

client.start()
client.loop.run_until_complete(main())
client.run_until_disconnected()
