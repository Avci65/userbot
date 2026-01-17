import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

print("API_ID ENV RAW:", repr(os.getenv("API_ID")))
print("API_HASH ENV RAW:", repr(os.getenv("API_HASH")))
print("SESSION ENV RAW:", repr(os.getenv("SESSION_STRING"))[:60])

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_STRING = os.getenv("SESSION_STRING", "")
SESSION_STRING = SESSION_STRING.replace("\n", "").replace("\r", "").strip()

print("API_ID:", API_ID)
print("HASH_LEN:", len(API_HASH))
print("SESSION_LEN:", len(SESSION_STRING))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

def is_owner(event):
    return OWNER_ID == 0 or event.sender_id == OWNER_ID


if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r"\.ping"))
async def ping(event):
    if not is_owner(event):
        return
    await event.reply("pong ✅")

client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
