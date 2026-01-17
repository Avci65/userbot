import os
import asyncio
import random
import string
from io import BytesIO

import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from PIL import Image

# ---------------- ENV ----------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_STRING = os.getenv("SESSION_STRING", "")
SESSION_STRING = SESSION_STRING.replace("\n", "").replace("\r", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Telegram user ID
QUOTLY_BOT = os.getenv("QUOTLY_BOT", "QuotLyBot").strip().lstrip("@")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

def is_owner(event) -> bool:
    return OWNER_ID == 0 or event.sender_id == OWNER_ID

if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------------- Helpers ----------------
def _rand_pack_suffix(n=10):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def _get_bot_username():
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=30).json()
    if not r.get("ok"):
        raise RuntimeError("BOT_TOKEN hatalı olabilir (getMe başarısız).")
    return r["result"]["username"]  # örn MyStickerBot

def _create_sticker_set(user_id: int, name: str, title: str, png_sticker_path: str, emoji="😄"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createNewStickerSet"
    with open(png_sticker_path, "rb") as f:
        files = {"png_sticker": f}
        data = {"user_id": user_id, "name": name, "title": title, "emojis": emoji}
        return requests.post(url, data=data, files=files, timeout=60).json()

# ---------------- Commands ----------------

# ✅ QuotLy Sticker
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

    # Mesajı forward et ve forward id al
    fwd = await client.forward_messages(bot_entity, replied)
    fwd_id = fwd.id if hasattr(fwd, "id") else fwd[0].id

    sticker_msg = None
    for _ in range(40):  # 20 saniye
        await asyncio.sleep(0.5)

        # sadece forward sonrası gelenleri ara
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


# ✅ Dizla: Sticker pack oluştur
@client.on(events.NewMessage(pattern=r"(?i)^\.(dızla|dizla)\s*$"))
async def cmd_dizla(event):
    if not is_owner(event):
        return

    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok! BotFather tokenini Railway Variables'a ekle.")

    if not event.is_reply:
        return await event.reply("Bir **sticker'a** yanıt verip `.dizla` yaz 😄")

    replied = await event.get_reply_message()
    if not replied.sticker:
        return await event.reply("❌ Sticker'a reply yapmalısın.")

    status = await event.reply("🛠️ Stickerini çalışıyorum...")

    # Sticker indir (webp)
    webp_path = await client.download_media(replied, file="in.webp")

    # Webp -> PNG
    im = Image.open(webp_path).convert("RGBA")
    png_path = "sticker.png"
    im.save(png_path, "PNG")

    # ✅ pack name mutlaka _by_<BOT_USERNAME> ile bitmeli
    try:
        bot_username = _get_bot_username()
    except Exception as e:
        return await status.edit(f"❌ BOT_USERNAME alınamadı: {e}")

    suffix = _rand_pack_suffix(10)
    pack_name = f"dizla_{suffix}_by_{bot_username}".lower()  # ✅ doğru format
    pack_title = f"Abdullah Dizla Pack {suffix} 😄"

    res = _create_sticker_set(OWNER_ID, pack_name, pack_title, png_path, emoji="😄")

    if not res.get("ok"):
        err = res.get("description", "Bilinmeyen hata")
        return await status.edit(f"❌ Paket oluşturulamadı: {err}")

    pack_link = f"https://t.me/addstickers/{pack_name}"
    await status.edit(f"✅ Paket oluşturuldu!\n🔗 {pack_link}")


# ---------------- Start ----------------
client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
