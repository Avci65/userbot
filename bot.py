import os
import asyncio
import random
import string
import requests
import redis

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from PIL import Image

# ---------------- ENV ----------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_STRING = os.getenv("SESSION_STRING", "")
SESSION_STRING = SESSION_STRING.replace("\n", "").replace("\r", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))
QUOTLY_BOT = os.getenv("QUOTLY_BOT", "QuotLyBot").strip().lstrip("@")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REDIS_URL = os.getenv("REDIS_URL", "").strip()

# ---------------- Redis ----------------
rdb = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

def redis_get_pack(pack_key: str):
    if not rdb:
        return None
    return rdb.get(f"pack:{pack_key}")

def redis_set_pack(pack_key: str, pack_name: str):
    if not rdb:
        return
    rdb.set(f"pack:{pack_key}", pack_name)

# ---------------- Base ----------------
def is_owner(event) -> bool:
    return OWNER_ID == 0 or event.sender_id == OWNER_ID

if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------------- Bot API Helpers ----------------
BOT_USERNAME_CACHE = None

def _rand_pack_suffix(n=10):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def _get_bot_username():
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=30).json()
    if not r.get("ok"):
        raise RuntimeError("BOT_TOKEN hatalı olabilir (getMe başarısız).")
    return r["result"]["username"]

def _get_bot_username_cached():
    global BOT_USERNAME_CACHE
    if BOT_USERNAME_CACHE:
        return BOT_USERNAME_CACHE
    BOT_USERNAME_CACHE = _get_bot_username()
    return BOT_USERNAME_CACHE

def botapi_delete_webhook():
    # getUpdates çalışsın diye
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    try:
        requests.post(url, timeout=15)
    except:
        pass

def botapi_get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 10}
    if offset is not None:
        params["offset"] = offset
    return requests.get(url, params=params, timeout=20).json()

def botapi_delete_sticker(file_id: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteStickerFromSet"
    return requests.post(url, data={"sticker": file_id}, timeout=30).json()

def _create_sticker_set(user_id: int, name: str, title: str, png_sticker_path: str, emoji="😄"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/createNewStickerSet"
    with open(png_sticker_path, "rb") as f:
        files = {"png_sticker": f}
        data = {"user_id": user_id, "name": name, "title": title, "emojis": emoji}
        return requests.post(url, data=data, files=files, timeout=60).json()

def _add_sticker_to_set(user_id: int, name: str, png_sticker_path: str, emoji="😄"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/addStickerToSet"
    with open(png_sticker_path, "rb") as f:
        files = {"png_sticker": f}
        data = {"user_id": user_id, "name": name, "emojis": emoji}
        return requests.post(url, data=data, files=files, timeout=60).json()

# ✅ webhook kapat (sil komutu için getUpdates şart)
botapi_delete_webhook()

# ---------------- Commands ----------------

# ✅ .q (ilk çalışan mantık birebir)
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
        msgs = await client.get_messages(bot_entity, min_id=fwd_id, limit=20)
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


# ✅ .dizla / .dızla (Redis ile sabit pack)
@client.on(events.NewMessage(pattern=r"(?i)^\.(dızla|dizla)(?:\s+(.+))?\s*$"))
async def cmd_dizla(event):
    if not is_owner(event):
        return

    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok! Railway Variables'a ekle.")

    if not REDIS_URL or not rdb:
        return await event.reply("❌ REDIS_URL yok! Railway'e Redis service eklemelisin.")

    if not event.is_reply:
        return await event.reply("Sticker'a reply yapıp `.dizla 1` veya `.dizla meme` yaz 😄")

    replied = await event.get_reply_message()
    if not replied.sticker:
        return await event.reply("❌ Sticker'a reply yapmalısın.")

    arg = (event.pattern_match.group(2) or "").strip().lower() or "1"
    status = await event.reply(f"🛠️ Stickerini çalışıyorum... (pack: {arg})")

    webp_path = await client.download_media(replied, file="in.webp")
    im = Image.open(webp_path).convert("RGBA")
    png_path = "sticker.png"
    im.save(png_path, "PNG")

    bot_username = _get_bot_username_cached()
    pack_name = redis_get_pack(arg)

    # Pack varsa ekle
    if pack_name:
        res = _add_sticker_to_set(OWNER_ID, pack_name, png_path, emoji="😄")
        if not res.get("ok"):
            err = res.get("description", "Bilinmeyen hata")
            return await status.edit(f"❌ Pack'e eklenemedi: {err}")

        pack_link = f"https://t.me/addstickers/{pack_name}"
        return await status.edit(f"✅ Sticker eklendi! ({arg})\n🔗 {pack_link}")

    # Pack yoksa oluştur
    suffix = _rand_pack_suffix(10)
    pack_name = f"dizla_{arg}_{suffix}_by_{bot_username}".lower()
    pack_title = f"Abdullah Dizla - {arg.upper()} 😄"

    res = _create_sticker_set(OWNER_ID, pack_name, pack_title, png_path, emoji="😄")
    if not res.get("ok"):
        err = res.get("description", "Bilinmeyen hata")
        return await status.edit(f"❌ Paket oluşturulamadı: {err}")

    redis_set_pack(arg, pack_name)
    pack_link = f"https://t.me/addstickers/{pack_name}"
    return await status.edit(f"✅ Paket oluşturuldu ve kaydedildi! ({arg})\n🔗 {pack_link}")


# ✅ .sil / .sil 1 (bot updates ile %100 file_id)
@client.on(events.NewMessage(pattern=r"(?i)^\.(sil)(?:\s+(.+))?\s*$"))
async def cmd_sil(event):
    if not is_owner(event):
        return

    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok!")

    if not event.is_reply:
        return await event.reply("Silmek istediğin **sticker'a reply** yapıp `.sil` yaz.")

    replied = await event.get_reply_message()
    if not replied.sticker:
        return await event.reply("❌ Sticker'a reply yapmalısın.")

    status = await event.reply("🗑️ Sticker siliniyor...")

    # 1) mevcut update offset al
    up = botapi_get_updates()
    last_update_id = 0
    if up.get("ok") and up.get("result"):
        last_update_id = up["result"][-1]["update_id"]

    # 2) stickerı bot'a DM at
    bot_username = _get_bot_username_cached()
    bot_entity = await client.get_entity(bot_username)
    await client.send_file(bot_entity, replied)

    # 3) bot getUpdates içinden sticker file_id yakala
    sticker_file_id = None
    for _ in range(30):  # 15sn
        await asyncio.sleep(0.5)
        res = botapi_get_updates(offset=last_update_id + 1)
        if not res.get("ok"):
            continue

        for item in res.get("result", []):
            msg = item.get("message") or item.get("edited_message")
            if msg and "sticker" in msg:
                sticker_file_id = msg["sticker"]["file_id"]
                break

        if sticker_file_id:
            break

    if not sticker_file_id:
        return await status.edit("❌ file_id alınamadı. (getUpdates boş olabilir)")

    # 4) sil
    del_res = botapi_delete_sticker(sticker_file_id)
    if not del_res.get("ok"):
        err = del_res.get("description", "Bilinmeyen hata")
        return await status.edit(f"❌ Silinemedi: {err}")

    await status.edit("✅ Sticker silindi!")

# ---------------- Start ----------------
client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
