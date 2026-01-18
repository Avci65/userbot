import os
import json
import time
import asyncio
import random
import string
import threading

import requests
import redis
from flask import Flask, request

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

if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

# ---------------- Redis ----------------
rdb = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# ---------------- Telethon Client ----------------
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def is_owner(event) -> bool:
    return OWNER_ID == 0 or event.sender_id == OWNER_ID

# ---------------- Helpers ----------------
BOT_USERNAME_CACHE = None

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

def _rand_pack_suffix(n=10):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def botapi_delete_webhook():
    # .sil getUpdates vs için lazım olabiliyor ama inline için gerek yok.
    # Yine de senin mevcut sistem için kapatmıyoruz.
    return

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

def redis_get_pack(pack_key: str):
    if not rdb:
        return None
    return rdb.get(f"pack:{pack_key}")

def redis_set_pack(pack_key: str, pack_name: str):
    if not rdb:
        return
    rdb.set(f"pack:{pack_key}", pack_name)

# ---------------- Flask Webhook Server ----------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "ok", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json or {}

    # 1) INLINE QUERY
    if "inline_query" in update:
        iq = update["inline_query"]
        iq_id = iq.get("id")
        from_user = iq.get("from", {})
        q = (iq.get("query") or "").strip()

        # Beklenen format:
        # "selam @avci65"
        # "selam 895969250"
        parts = q.split()
        if len(parts) < 2:
            return _answer_inline(iq_id, [])
        target = parts[-1]
        msg = " ".join(parts[:-1]).strip()

        # target normalize
        if target.startswith("@"):
            target = target[1:]

        # id / username kayıt
        wid = str(int(time.time() * 1000))
        if rdb:
            rdb.setex(f"whisper:{wid}", 3600, json.dumps({
                "target": target,
                "msg": msg
            }))
        else:
            # redis yoksa sonuç döndürmeyelim
            return _answer_inline(iq_id, [])

        # inline result: butonlu kart
        result = [{
            "type": "article",
            "id": wid,
            "title": f"🤫 Gizli mesaj → {target}",
            "description": msg[:60],
            "input_message_content": {
                "message_text": f"🤫 {target} için gizli mesaj var!",
                "parse_mode": "HTML"
            },
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "👀 Mesajı Gör", "callback_data": f"whisper:{wid}"}
                ]]
            }
        }]
        return _answer_inline(iq_id, result)

    # 2) CALLBACK QUERY
    cq = update.get("callback_query")
    if cq:
        cb_id = cq.get("id")
        data = cq.get("data", "")
        from_user = cq.get("from", {})
        from_id = from_user.get("id")

        if not data.startswith("whisper:"):
            return _answer_callback(cb_id, "❌ Bilinmeyen buton", True)

        if not rdb:
            return _answer_callback(cb_id, "❌ Redis yok", True)

        wid = data.split(":", 1)[1]
        payload = rdb.get(f"whisper:{wid}")
        if not payload:
            return _answer_callback(cb_id, "⏳ Bu fısıltı süresi dolmuş.", True)

        payload = json.loads(payload)
        target = payload["target"]
        msg = payload["msg"]

        # hedefi resolve et
        # - eğer target sayı ise: id
        # - değilse username
        ok = False
        if str(from_id) == str(target):
            ok = True
        else:
            # username karşılaştırması için from_user username kontrol
            fu = (from_user.get("username") or "").lower()
            if fu and fu == str(target).lower():
                ok = True

        if not ok:
            return _answer_callback(cb_id, "❌ Bu mesaj sana değil 😄", True)

        if len(msg) > 190:
            msg = msg[:190] + "…"

        return _answer_callback(cb_id, f"🤫 Gizli mesaj:\n{msg}", True)

    return "ok", 200

def _answer_inline(inline_query_id, results):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerInlineQuery"
    payload = {
        "inline_query_id": inline_query_id,
        "results": json.dumps(results),
        "cache_time": 0,
        "is_personal": True
    }
    requests.post(url, data=payload, timeout=20)
    return "ok", 200

def _answer_callback(callback_query_id, text, alert=True):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    requests.post(url, data={
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": alert
    }, timeout=20)
    return "ok", 200

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)

# ---------------- Commands (senin komutların) ----------------

# ✅ .q / .q 3
@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(q)(?:\s+(\d+))?\s*$"))
async def cmd_q(event):
    if not is_owner(event):
        return

    if not event.is_reply:
        return await event.reply("Bir mesaja yanıt verip `.q` yaz ✅\nÖrn: `.q` / `.q 3`")

    replied = await event.get_reply_message()
    n_str = event.pattern_match.group(2)
    n = int(n_str) if n_str else 1
    n = max(1, min(n, 10))

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

    if n == 1:
        fwd = await client.forward_messages(bot_entity, replied)
        fwd_id = fwd.id if hasattr(fwd, "id") else fwd[0].id

        sticker = await wait_for_sticker(fwd_id)
        if not sticker:
            return await status.edit("❌ QuotLy sticker göndermedi. (45sn)")

        await client.send_file(event.chat_id, sticker, force_document=False)
        await status.delete()
        return

    start_id = replied.id
    msgs = await client.get_messages(event.chat_id, min_id=start_id - 1, limit=n + 15)
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

# ✅ .dizla
@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(dızla|dizla)(?:\s+(.+))?\s*$"))
async def cmd_dizla(event):
    if not is_owner(event):
        return
    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok!")
    if not REDIS_URL or not rdb:
        return await event.reply("❌ REDIS_URL yok! Railway'e Redis service ekle.")

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

    if pack_name:
        res = _add_sticker_to_set(OWNER_ID, pack_name, png_path, emoji="😄")
        if not res.get("ok"):
            return await status.edit(f"❌ Pack'e eklenemedi: {res.get('description')}")
        return await status.edit(f"✅ Sticker eklendi! ({arg})\n🔗 https://t.me/addstickers/{pack_name}")

    suffix = _rand_pack_suffix(10)
    pack_name = f"dizla_{arg}_{suffix}_by_{bot_username}".lower()
    pack_title = f"Abdullah Dizla - {arg.upper()} 😄"

    res = _create_sticker_set(OWNER_ID, pack_name, pack_title, png_path, emoji="😄")
    if not res.get("ok"):
        return await status.edit(f"❌ Paket oluşturulamadı: {res.get('description')}")

    redis_set_pack(arg, pack_name)
    return await status.edit(f"✅ Paket oluşturuldu! ({arg})\n🔗 https://t.me/addstickers/{pack_name}")

# ✅ .sil
@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(sil)\s*$"))
async def cmd_sil(event):
    if not is_owner(event):
        return
    if not BOT_TOKEN:
        return await event.reply("❌ BOT_TOKEN yok!")

    if not event.is_reply:
        return await event.reply("Silmek istediğin sticker'a reply yapıp `.sil` yaz.")

    replied = await event.get_reply_message()
    if not replied.sticker:
        return await event.reply("❌ Sticker'a reply yapmalısın.")

    status = await event.reply("🗑️ Sticker siliniyor...")

    up = botapi_get_updates()
    last_update_id = 0
    if up.get("ok") and up.get("result"):
        last_update_id = up["result"][-1]["update_id"]

    bot_username = _get_bot_username_cached()
    bot_entity = await client.get_entity(bot_username)
    await client.send_file(bot_entity, replied)

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
        return await status.edit("❌ file_id alınamadı.")

    del_res = botapi_delete_sticker(sticker_file_id)
    if not del_res.get("ok"):
        return await status.edit(f"❌ Silinemedi: {del_res.get('description')}")

    await status.edit("✅ Sticker silindi!")

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.özel\s+(.+)\s+(\S+)$"))
async def cmd_auto_whisper_inline(event):
    if not is_owner(event):
        return

    msg_content = event.pattern_match.group(1).strip()
    target = event.pattern_match.group(2).strip()
    clean_target = target.lstrip("@")

    # 1) Önce mesajı Redis'e kaydet (Mevcut mantık)
    wid = str(int(time.time() * 1000))
    if rdb:
        rdb.setex(f"whisper:{wid}", 3600, json.dumps({
            "target": clean_target,
            "msg": msg_content
        }))
    else:
        return await event.edit("❌ Redis yok!")

    # 2) Kendi hesabın üzerinden "inline query" sonucunu grupta paylaş
    bot_username = _get_bot_username_cached()
    
    try:
        # Userbot senin adına botu çağırır ve sonucu gruba atar
        results = await client.inline_query(bot_username, f"{msg_content} {target}")
        await results[0].click(event.chat_id)
        
        # Orijinal ".özel" komutunu sil
        await event.delete()
    except Exception as e:
        await event.edit(f"❌ Hata: {str(e)}\nNot: Botun 'Inline Mode' özelliği kapalı olabilir.")

# ---------------- Plugins ----------------
try:
    from plugins.sa import setup as sa_setup
    sa_setup(client)
except:
    pass

try:
    from plugins.ig import setup as ig_setup
    ig_setup(client)
except:
    pass

# ---------------- Start ----------------
t = threading.Thread(target=run_flask, daemon=True)
t.start()
print("✅ Flask server başladı (webhook)")

client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
