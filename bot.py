import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ---------------- ENV ----------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_STRING = os.getenv("SESSION_STRING", "")
SESSION_STRING = SESSION_STRING.replace("\n", "").replace("\r", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Telegram ID'n (Railway Variables'a ekle)
QUOTLY_BOT = os.getenv("QUOTLY_BOT", "QuotLyBot").strip().lstrip("@")

def is_owner(event) -> bool:
    return OWNER_ID == 0 or event.sender_id == OWNER_ID

if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------------- Commands ----------------
@client.on(events.NewMessage(pattern=r"(?i)^\.(q)\s*$"))
async def cmd_q(event):
    if not is_owner(event):
        return

    if not event.is_reply:
        return await event.reply("Bir mesaja yanıt verip `.q` yaz ✅")

    replied = await event.get_reply_message()
    text = (replied.raw_text or "").strip()
    if not text:
        return await event.reply("Bu mesajda metin yok 😅")

    status = await event.reply("✅ QuotLy sticker hazırlanıyor...")

    bot_entity = await client.get_entity(QUOTLY_BOT)

    # ✅ Mesajı forward et ve forward ID'sini al
    fwd = await client.forward_messages(bot_entity, replied)
    fwd_id = fwd.id if hasattr(fwd, "id") else fwd[0].id

    # ✅ sadece bu forward'dan SONRA gelen stickerı yakala
    sticker_msg = None
    for _ in range(40):  # 20sn
        await asyncio.sleep(0.5)

        # forward edilen mesajdan daha yeni mesajları al
        msgs = await client.get_messages(bot_entity, min_id=fwd_id, limit=10)

        for m in msgs:
            if m.sticker or (m.file and m.file.mime_type == "image/webp"):
                sticker_msg = m
                break

        if sticker_msg:
            break

    if not sticker_msg:
        return await status.edit("❌ QuotLy sticker göndermedi. (20sn)")

    await client.send_file(event.chat_id, sticker_msg, force_document=False)
    await status.delete()


# ---------------- Start ----------------
client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
