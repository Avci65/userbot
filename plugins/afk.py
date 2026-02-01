import os
import time
from collections import defaultdict

from telethon import events
from telethon.tl.types import MessageEntityMentionName

from plugins._help import add_help


def setup(client):
    print("✅ afk.py plugin yüklendi")

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    # Cooldown (saniye) - istersen Railway ENV: AFK_COOLDOWN=30
    AFK_COOLDOWN = int(os.getenv("AFK_COOLDOWN", "30"))

    # AFK state
    afk = {
        "on": False,
        "since": 0,
        "reason": ""
    }

    me_id = {"id": None}

    # Stats & anti-spam
    last_notify = {}  # (sender_id, kind) -> last_ts
    stats = {
        "reply": defaultdict(int),   # sender_id -> count
        "mention": defaultdict(int), # sender_id -> count
        "all": defaultdict(int),     # sender_id -> total
        "last_text": {}              # sender_id -> last message preview
    }

    async def ensure_me():
        if me_id["id"] is None:
            me = await client.get_me()
            me_id["id"] = me.id
        return me_id["id"]

    def fmt_duration(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}dk"
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}sa {minutes}dk"

    def clean_preview(text: str, maxlen: int = 120) -> str:
        t = (text or "").strip().replace("\n", " ")
        return (t[:maxlen] + "…") if len(t) > maxlen else t

    def is_mention_of_me(msg) -> bool:
        # Telethon bazen mentioned flag'i koyar
        try:
            if getattr(msg, "mentioned", False):
                return True
        except:
            pass

        # Entity ile kontrol (mention name)
        if msg.entities:
            for ent in msg.entities:
                if isinstance(ent, MessageEntityMentionName):
                    if ent.user_id == me_id["id"]:
                        return True
        return False

    async def is_reply_to_me(event) -> bool:
        if not event.is_reply:
            return False
        try:
            r = await event.get_reply_message()
            if not r:
                return False
            return r.sender_id == me_id["id"]
        except:
            return False

    def can_notify(sender_id: int, kind: str) -> bool:
        # sender+kind bazında cooldown
        now = int(time.time())
        key = (sender_id, kind)
        last = last_notify.get(key, 0)
        if now - last < AFK_COOLDOWN:
            return False
        last_notify[key] = now
        return True

    async def sender_display(sender):
        name = (getattr(sender, "first_name", "") or "").strip()
        username = getattr(sender, "username", None)
        if name:
            return name
        if username:
            return "@" + username
        return str(sender.id)

    async def notify_owner(event, kind: str):
        sender = await event.get_sender()
        chat = await event.get_chat()

        sid = event.sender_id
        if not can_notify(sid, kind):
            return

        chat_title = getattr(chat, "title", None) or "Özel Sohbet"
        who = await sender_display(sender)

        msg_text = event.raw_text or ""
        preview = clean_preview(msg_text)

        # stats
        stats["all"][sid] += 1
        stats[kind][sid] += 1
        stats["last_text"][sid] = preview

        since_s = int(time.time() - afk["since"]) if afk["since"] else 0
        dur = fmt_duration(since_s)
        reason = afk["reason"].strip()
        reason_line = f"\n📝 Sebep: {reason}" if reason else ""

        out = (
            f"📩 AFK iken mesaj aldın ({kind})\n"
            f"👤 {who}\n"
            f"🏷️ Grup: {chat_title}\n"
            f"⏱️ AFK: {dur}{reason_line}\n\n"
            f"💬 Mesaj:\n{preview}"
        )

        # ✅ en garantisi: Saved Messages
        await client.send_message("me", out)

    async def send_summary():
        # AFK kapatınca özet (Saved Messages)
        total = sum(stats["all"].values())
        if total == 0:
            await client.send_message("me", "ℹ️ AFK süresince sana reply/mention gelmedi.")
            return

        # top senders (total)
        top = sorted(stats["all"].items(), key=lambda x: x[1], reverse=True)[:15]

        lines = []
        for sid, cnt in top:
            # isim çekelim
            try:
                sender = await client.get_entity(sid)
                who = await sender_display(sender)
            except:
                who = str(sid)

            r = stats["reply"].get(sid, 0)
            m = stats["mention"].get(sid, 0)
            last = stats["last_text"].get(sid, "")
            last_line = f" — “{last}”" if last else ""
            lines.append(f"• {who}: {cnt} (reply:{r}, mention:{m}){last_line}")

        since_s = int(time.time() - afk["since"]) if afk["since"] else 0
        dur = fmt_duration(since_s)
        reason = afk["reason"].strip()
        reason_line = f"\n📝 Sebep: {reason}" if reason else ""

        text = (
            f"📊 AFK ÖZET\n"
            f"⏱️ Süre: {dur}{reason_line}\n"
            f"📦 Toplam bildirim sayılan mesaj: {total}\n\n"
            f"🏆 En çok yazanlar:\n" + "\n".join(lines)
        )

        await client.send_message("me", text)

    def reset_stats():
        last_notify.clear()
        stats["reply"].clear()
        stats["mention"].clear()
        stats["all"].clear()
        stats["last_text"].clear()

    # -------------------
    # .afk komutu
    # -------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(afk)(?:\s+(.+))?\s*$"))
    async def afk_handler(event):
        if OWNER_ID != 0 and event.sender_id != OWNER_ID:
            return
        await ensure_me()

        reason = event.pattern_match.group(2) or ""
        afk["on"] = True
        afk["since"] = int(time.time())
        afk["reason"] = reason.strip()

        reset_stats()

        if afk["reason"]:
            await event.edit(f"✅ AFK moduna geçtin.\n📝 Sebep: {afk['reason']}\n⏳ Cooldown: {AFK_COOLDOWN}s")
        else:
            await event.edit(f"✅ AFK moduna geçtin.\n⏳ Cooldown: {AFK_COOLDOWN}s")

    # -------------------
    # .back komutu
    # -------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(back)\s*$"))
    async def back_handler(event):
        if OWNER_ID != 0 and event.sender_id != OWNER_ID:
            return
        await ensure_me()

        if not afk["on"]:
            await event.edit("ℹ️ Zaten AFK değilsin.")
            return

        # önce özet gönder
        await send_summary()

        # sonra kapat
        since_s = int(time.time() - afk["since"]) if afk["since"] else 0
        dur = fmt_duration(since_s)

        afk["on"] = False
        afk["since"] = 0
        afk["reason"] = ""

        reset_stats()

        await event.edit(f"✅ AFK kapatıldı.\n⏱️ Süre: {dur}")

    # -------------------
    # AFK iken gelen mesajları yakala
    # -------------------
    @client.on(events.NewMessage(incoming=True))
    async def afk_watch(event):
        await ensure_me()

        if not afk["on"]:
            return

        # kendinden geliyorsa
        if event.sender_id == me_id["id"]:
            return

        msg = event.message
        if not msg:
            return

        reply_to_me = await is_reply_to_me(event)
        mention_me = is_mention_of_me(msg)

        if reply_to_me:
            await notify_owner(event, "reply")
        elif mention_me:
            await notify_owner(event, "mention")


add_help(
    "AFK",
    ".afk [sebep]\n.back",
    "AFK modunu açar/kapatır. AFK iken reply/mention olursa Saved Messages'a bildirim düşer. "
    "Spam engeli için cooldown vardır (ENV: AFK_COOLDOWN)."
)
