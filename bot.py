import os
import asyncio
import random
import string
import time
import json
import threading

import requests
import redis

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from PIL import Image

from flask import Flask, request


# =========================================================
# Flask webhook server
# =========================================================
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "ok", 200


def _answer_callback(cb_id, text, alert=True):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, data={
            "callback_query_id": cb_id,
            "text": text,
            "show_alert": alert
        }, timeout=15)
    except:
        pass


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json or {}

    # ✅ CALLBACK QUERY (button click)
    cq = update.get("callback_query")
    if not cq:
        return "ok", 200

    cb_id = cq.get("id")
    data = cq.get("data", "")
    from_user = cq.get("from", {})
    from_id = from_user.get("id")

    if not data.startswith("whisper:"):
        _answer_callback(cb_id, "❌ Bilinmeyen buton", True)
        return "ok", 200

    wid = data.split(":", 1)[1]
    key = f"whisper:{wid}"

    if not rdb:
        _answer_callback(cb_id, "❌ Redis yok", True)
        return "ok", 200

    payload = rdb.get(key)
    if not payload:
        _answer_callback(cb_id, "⏳ Bu fısıltı süresi dolmuş.", True)
        return "ok", 200

    payload = json.loads(payload)
    target_id = int(payload["target_id"])
    msg = payload["msg"]

    # ✅ sadece hedef kişi görsün
    if from_id != target_id:
        _answer_callback(cb_id, "❌ Bu mesaj sana değil 😄", True)
        return "ok", 200

    if len(msg) > 190:
        msg = msg[:190] + "…"

    _answer_callback(cb_id, f"🤫 Gizli mesaj:\n{msg}", True)
    return "ok", 200


def run_flask():
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)


# =========================================================
# ENV
# =========================================================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_STRING = os.getenv("SESSION_STRING", "")
SESSION_STRING = SESSION_STRING.replace("\n", "").replace("\r", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))
QUOTLY_BOT = os.getenv("QUOTLY_BOT", "QuotLyBot").strip().lstrip("@")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REDIS_URL = os.getenv("REDIS_URL", "").strip()

if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN yok! .sil / .dizla / .özel çalışmaz.")


# =========================================================
# Redis
# =========================================================
rdb = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

def redis_get_pack(pack_key: str):
    if not rdb:
        return None
    return rdb.get(f"pack:{pack_key}")

def redis_set_pack(pack_key: str, pack_name: str):
    if not rdb:
        return
    rdb.set(f"pack:{pack_key}", pack_name)


# =========================================================
# Telethon Client
# =========================================================
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)


def is_owner(event) -> bool:
    return OWNER_ID == 0 or event.sender_id == OWNER_ID


# =========================================================
# Bot API Helpers
# =========================================================
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
    # getUpdates çalışsın diye kapat
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


# ✅ delete webhook (sil için)
botapi_delete_webhook()


# =========================================================
# .q / .q 3
# =========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(q)(?:\s+(\d+))?\s*$"))
async def cmd_q(event):
    if not is_owner(event):
        return

    if not event.is_reply:
        return await event.reply("Bir mesaja yanıt verip `.q` yaz ✅\nÖrn: `.q` / `.q 3`")

    replied = await event.get_reply_message()

    n_str = event.pattern_match.group(2)
    n = int(n_str) if n_str else 1
    n = max(1, min(n, 10))  # 1..10

    status = await event.reply("✅ QuotLy sticker hazırlanıyor...")
    bot_entity = await client.get_entity(QUOTLY_BOT)

    async def wait_for_sticker(min_id: int, timeout=45):
        for _ in range(int(timeout / 0.5)):
            await asyncio.sleep(0.5)
            msgs = await client.get_messages(bot_entity, min_id=min_id, limit=30)
            for m in msgs:
                if m.sticker or (m.file and m.file.mime_type == "image/webp"):
                    return m
        return None

    # tek mesaj
    if n == 1:
        fwd = await client.forward_messages(bot_entity, replied)
        fwd_id = fwd.id if hasattr(fwd, "id") else fwd[0].id

        sticker = await wait_for_sticker(fwd_id)
        if not sticker:
            return await status.edit("❌ QuotLy sticker göndermedi. (45sn)")

        await client.send_file(event.chat_id, sticker, force_document=False)
        await status.delete()
        return

    # çoklu mesaj
    start_id = replied.id
    msgs = await client.get_messages(event.chat_id, min_id=start_id - 1, limit=n + 20)
    msgs = sorted(msgs, key=lambda m: m.id)
    msgs = [m for m in msgs if m.id >= start_id][:n]

    if not msgs:
        return await status.edit("❌ Mesaj bulunamadı.")

    fwd_list = await client.forward_messages(bot_entity, msgs)
    last_fwd_id = fwd_list[-1].id if isinstance(fwd_list, list) else fwd_list.id

    sticker = await wait_for_sticker(last_fwd_id)
    if not sticker:
        return await status.edit("❌ QuotLy sticker göndermedi. (45sn)")

    await client.send_file(event.chat_id, sticker, force_document=False)
    await status.delete()


# =========================================================
# .dizla / .dızla
# =========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(dızla|dizla)(?:\s+(.+))?\s*$"))
async def cmd_dizla(event):
    if not is_owner(event):
        return

    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok!")

    if not REDIS_URL or not rdb:
        return await event.reply("❌ REDIS_URL yok! Railway'e Redis service eklemelisin.")

    if not event.is_reply:
        return await event.reply("Sticker'a reply yapıp `.dizla 1` veya `.dizla meme` yaz 😄")

    replied = await event.get_reply_message()
    if not replied.sticker:
        return await event.reply("❌ Sticker'a reply yapmalısın.")

    arg = (event.pattern_match.group(2) or "").strip().lower() or "1"
    status = await event.reply(f"🛠️ Sticker ekleniyor... (pack: {arg})")

    webp_path = await client.download_media(replied, file="in.webp")
    im = Image.open(webp_path).convert("RGBA")
    png_path = "sticker.png"
    im.save(png_path, "PNG")

    bot_username = _get_bot_username_cached()
    pack_name = redis_get_pack(arg)

    # varsa ekle
    if pack_name:
        res = _add_sticker_to_set(OWNER_ID, pack_name, png_path, emoji="😄")
        if not res.get("ok"):
            err = res.get("description", "Bilinmeyen hata")
            return await status.edit(f"❌ Pack'e eklenemedi: {err}")

        pack_link = f"https://t.me/addstickers/{pack_name}"
        return await status.edit(f"✅ Sticker eklendi! ({arg})\n🔗 {pack_link}")

    # yoksa oluştur
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


# =========================================================
# .sil
# =========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(sil)\s*$"))
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

    # update offset al
    up = botapi_get_updates()
    last_update_id = 0
    if up.get("ok") and up.get("result"):
        last_update_id = up["result"][-1]["update_id"]

    # stickerı bot'a DM at
    bot_username = _get_bot_username_cached()
    bot_entity = await client.get_entity(bot_username)
    await client.send_file(bot_entity, replied)

    # file_id yakala
    sticker_file_id = None
    for _ in range(30):
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

    del_res = botapi_delete_sticker(sticker_file_id)
    if not del_res.get("ok"):
        err = del_res.get("description", "Bilinmeyen hata")
        return await status.edit(f"❌ Silinemedi: {err}")

    await status.edit("✅ Sticker silindi!")


# =========================================================
# .özel
# =========================================================
@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(özel|ozel)\s+(.+)$"))
async def cmd_ozel(event):
    if not is_owner(event):
        return

    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok!")

    if not rdb:
        return await event.reply("❌ Redis yok! Whisper için Redis şart.")

    raw = (event.pattern_match.group(2) or "").strip()
    parts = raw.split()
    if len(parts) < 2:
        return await event.reply("Kullanım: `.özel <mesaj> <id veya @username>`")

    target = parts[-1].strip()
    msg = " ".join(parts[:-1]).strip()

    if target.startswith("@"):
        target = target[1:].strip()

    try:
        entity = await client.get_entity(int(target)) if target.isdigit() else await client.get_entity(target)
    except Exception as e:
        return await event.reply(f"❌ Kullanıcı bulunamadı: `{e}`")

    uid = entity.id
    uname = getattr(entity, "username", None)
    mention = f"@{uname}" if uname else f"[kullanıcı](tg://user?id={uid})"

    wid = str(int(time.time() * 1000))
    rdb.setex(f"whisper:{wid}", 3600, json.dumps({
        "target_id": uid,
        "msg": msg
    }))

    button = {
        "inline_keyboard": [[
            {"text": "👀 Mesajı Gör", "callback_data": f"whisper:{wid}"}
        ]]
    }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": event.chat_id,
        "text": f"🤫 {mention} için gizli mesaj var!",
        "reply_markup": json.dumps(button),
        "parse_mode": "Markdown"
    }

    res = requests.post(url, data=data, timeout=30).json()
    if not res.get("ok"):
        return await event.reply(f"❌ Bot mesaj atamadı: {res.get('description', res)}")

    await event.delete()


# =========================================================
# Plugins
# =========================================================
try:
    from plugins.sa import setup as sa_setup
    sa_setup(client)
    print("✅ sa.py plugin yüklendi")
except Exception as e:
    print("⚠️ sa plugin yüklenemedi:", e)

try:
    from plugins.ig import setup as ig_setup
    ig_setup(client)
    print("✅ ig.py plugin yüklendi")
except Exception as e:
    print("⚠️ ig plugin yüklenemedi:", e)


# =========================================================
# Start
# =========================================================
# ✅ Flask thread başlat
t = threading.Thread(target=run_flask, daemon=True)
t.start()
print("✅ Flask webhook server başladı")

client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
