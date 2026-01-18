import os
import json
import redis
import requests
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REDIS_URL = os.getenv("REDIS_URL", "").strip()
rdb = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

app = Flask(__name__)

def answer_callback(cid, text, alert=True):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    requests.post(url, data={
        "callback_query_id": cid,
        "text": text,
        "show_alert": alert
    }, timeout=15)

@app.route("/", methods=["GET"])
def home():
    return "ok", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json or {}

    # callback query mi?
    cq = update.get("callback_query")
    if not cq:
        return "ok", 200

    cb_id = cq.get("id")
    data = cq.get("data", "")
    from_user = cq.get("from", {})
    from_id = from_user.get("id")

    if not data.startswith("whisper:"):
        answer_callback(cb_id, "❌ Bilinmeyen buton", alert=True)
        return "ok", 200

    wid = data.split(":", 1)[1]
    key = f"whisper:{wid}"
    if not rdb:
        answer_callback(cb_id, "❌ Redis yok", alert=True)
        return "ok", 200

    payload = rdb.get(key)
    if not payload:
        answer_callback(cb_id, "❌ Bu fısıltı süresi dolmuş.", alert=True)
        return "ok", 200

    payload = json.loads(payload)
    target_id = int(payload["target_id"])
    msg = payload["msg"]

    # hedef kişi değilse gösterme
    if from_id != target_id:
        answer_callback(cb_id, "❌ Bu mesaj sana değil 😄", alert=True)
        return "ok", 200

    # ✅ sadece hedefe popup içinde göster
    # Çok uzunsa kısalt
    if len(msg) > 180:
        msg = msg[:180] + "…"

    answer_callback(cb_id, f"🤫 Gizli mesaj:\n{msg}", alert=True)
    return "ok", 200
