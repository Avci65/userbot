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

import time
import random
import string
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

def _rand_pack_suffix(n=8):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def _create_sticker_set(user_id: int, name: str, title: str, png_sticker_path: str, emoji="🔥"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createNewStickerSet"
    with open(png_sticker_path, "rb") as f:
        files = {"png_sticker": f}
        data = {
            "user_id": user_id,
            "name": name,
            "title": title,
            "emojis": emoji
        }
        r = requests.post(url, data=data, files=files, timeout=60)
    return r.json()

def _add_sticker_to_set(user_id: int, name: str, png_sticker_path: str, emoji="🔥"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/addStickerToSet"
    with open(png_sticker_path, "rb") as f:
        files = {"png_sticker": f}
        data = {
            "user_id": user_id,
            "name": name,
            "emojis": emoji
        }
        r = requests.post(url, data=data, files=files, timeout=60)
    return r.json()

@client.on(events.NewMessage(pattern=r"(?i)^\.(dızla|dizla)\s*$"))
async def cmd_dizla(event):
    if not is_owner(event):
        return

    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok! BotFather'dan token alıp Railway Variables'a ekle.")

    if not event.is_reply:
        return await event.reply("Bir **sticker'a** yanıt verip `.dızla` yaz 😄")

    replied = await event.get_reply_message()
    if not replied.sticker:
        return await event.reply("❌ Bu bir sticker değil. Sticker'a reply yapmalısın.")

    status = await event.reply("🛠️ Stickerini çalışıyorum...")

    # 1) Stickerı indir
    webp_path = await client.download_media(replied, file="in.webp")

    # 2) Bot API png istiyor → webp'yi pngye çevirelim (Pillow ile)
    from PIL import Image
    im = Image.open(webp_path).convert("RGBA")
    png_path = "sticker.png"
    im.save(png_path, "PNG")

    # 3) Paket adı ve başlık
    suffix = _rand_pack_suffix()
    pack_name = f"dizla_{suffix}_by_{(await client.get_me()).username or 'myuserbot'}"
    pack_title = f"Abdullah Dizla Pack {suffix} 😄"

    # 4) Sticker set oluştur
    res = _create_sticker_set(event.sender_id, pack_name, pack_title, png_path, emoji="😄")

    if not res.get("ok"):
        # Eğer set var vs ise hata verir
        err = res.get("description", "Bilinmeyen hata")
        return await status.edit(f"❌ Paket oluşturulamadı: {err}")

    await status.edit("✅ Paket oluşturuldu! Sticker ekleniyor...")

    # 5) İlk sticker zaten eklenmiş olur (createNewStickerSet ekler)
    # Link gönder
    pack_link = f"https://t.me/addstickers/{pack_name}"
    await event.reply(f"🎉 Sticker paketin hazır!\n🔗 {pack_link}")

    await status.delete()



# ---------------- Start ----------------
client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
