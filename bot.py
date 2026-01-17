import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

print("API_ID ENV RAW:", repr(os.getenv("API_ID")))
print("API_HASH ENV RAW:", repr(os.getenv("API_HASH")))
print("SESSION ENV RAW:", repr(os.getenv("SESSION_STRING"))[:60])

API_ID = int(os.getenv("1838931", "0"))
API_HASH = os.getenv("d8ed731e06dff557170f3b6a85640522", "").strip()
SESSION_STRING = os.getenv("1BJWap1wBu5_arM-Cj2Ok8C8ltxa9E-RMa4pHeCej9ZX6XtSp33pNeTNmWt7_Qz0mX53a9xm7-JOFyCwZNsEmglEXfa7c2I-xe0Aw0JVnEpazKEIHchHSZ2pdUtbPhoZfW4v_xjPNh9O-6soLVKNXlQ8EPnx--mCCE8i8Dcr2KAvorBZep238lZIAkkWgsc18LjoE4JNAZgyaj-9Mo47wc-kRv4LJ8Y8gyDYarnG0UJ4oualI9eInU4xqUykO3vjnJDtu5eQWMeO-ePGBuULl32N6zBFkl_0qcXqx-4tL2izX1--v_qSlEBuV-YUNRTS4j9PfmzILCvG31LSa2gPMFhpfwn68V48=", "").strip()


if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r"\.ping"))
async def ping(event):
    await event.reply("pong ✅")

client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
