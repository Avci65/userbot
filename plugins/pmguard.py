# plugins/pmguard.py
import time
from telethon import events
from plugins._help import add_help

# bot.py içinde rdb yoksa bile çalışsın diye local fallback
PMGUARD_ENABLED_LOCAL = False
ALLOWED_LOCAL = set()
PM_COUNTER = {}  # user_id -> {"count": int, "ts": float}

# spam limit
MAX_PM = 3
WINDOW_SEC = 60

def setup(client, rdb=None):

    def _key_enabled():
        return "pmguard:enabled"

    def _key_allow(uid: int):
        return f"pmguard:allow:{uid}"

    def _set_enabled(val: bool):
        global PMGUARD_ENABLED_LOCAL
        if rdb:
            rdb.set(_key_enabled(), "1" if val else "0")
        else:
            PMGUARD_ENABLED_LOCAL = val

    def _get_enabled() -> bool:
        global PMGUARD_ENABLED_LOCAL
        if rdb:
            return rdb.get(_key_enabled()) == "1"
        return PMGUARD_ENABLED_LOCAL

    def _allow_user(uid: int):
        if rdb:
            rdb.set(_key_allow(uid), "1")
        else:
            ALLOWED_LOCAL.add(uid)

    def _disallow_user(uid: int):
        if rdb:
            try:
                rdb.delete(_key_allow(uid))
            except:
                pass
        else:
            ALLOWED_LOCAL.discard(uid)

    def _is_allowed(uid: int) -> bool:
        if rdb:
            return rdb.get(_key_allow(uid)) == "1"
        return uid in ALLOWED_LOCAL

    # ---------------------------
    # .pmguard on/off
    # ---------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(pmguard)\s+(on|off)\s*$"))
    async def cmd_pmguard(event):
        mode = event.pattern_match.group(2).lower()

        if mode == "on":
            _set_enabled(True)
            return await event.edit("✅ PM Guard açıldı.")
        else:
            _set_enabled(False)
            return await event.edit("❎ PM Guard kapatıldı.")

    # ---------------------------
    # .allow (DM'de reply ile)
    # ---------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(allow)\s*$"))
    async def cmd_allow(event):
        if not event.is_private:
            return await event.edit("❌ `.allow` sadece özel mesajda kullanılır (DM).")

        replied = await event.get_reply_message()
        if not replied:
            return await event.edit("❌ `.allow` için bir mesaja reply yap.")

        uid = replied.sender_id
        _allow_user(uid)

        try:
            ent = await client.get_entity(uid)
            name = (getattr(ent, "first_name", None) or "User")
        except:
            name = "User"

        await event.edit(f"✅ `{name}` izinlilere eklendi. (whitelist)")

    # ---------------------------
    # .block (DM'de reply ile)
    # ---------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(block)\s*$"))
    async def cmd_block(event):
        if not event.is_private:
            return await event.edit("❌ `.block` sadece özel mesajda kullanılır (DM).")

        replied = await event.get_reply_message()
        if not replied:
            return await event.edit("❌ `.block` için bir mesaja reply yap.")

        uid = replied.sender_id

        # whitelistten çıkar
        _disallow_user(uid)

        try:
            await client.block_user(uid)
        except Exception as e:
            return await event.edit(f"❌ Block başarısız: `{str(e)}`")

        await event.edit("⛔ Kullanıcı blocklandı.")

    # ---------------------------
    # PM Guard Listener (incoming)
    # ---------------------------
    @client.on(events.NewMessage(incoming=True))
    async def pmguard_listener(event):
        # sadece özel mesajlar
        if not event.is_private:
            return

        uid = event.sender_id

        # kendimiz/servis mesajları vs
        if uid is None:
            return

        # PM Guard kapalıysa
        if not _get_enabled():
            return

        # izinli ise dokunma
        if _is_allowed(uid):
            return

        # sayaç
        now = time.time()
        info = PM_COUNTER.get(uid)
        if not info or (now - info["ts"] > WINDOW_SEC):
            info = {"count": 0, "ts": now}

        info["count"] += 1
        info["ts"] = now
        PM_COUNTER[uid] = info

        # ilk mesajda uyar
        if info["count"] == 1:
            await event.reply(
                "👮 **PM Guard aktif!**\n"
                "Buraya yazmadan önce izin alman gerekiyor.\n\n"
                "✅ İzin almak için: kısa bir sebep yaz.\n"
                "⛔ Spam devam ederse otomatik engelleneceksin."
            )
            return

        # limit aşarsa block
        if info["count"] >= MAX_PM:
            try:
                await event.reply("⛔ Spam algılandı. Engellendin.")
            except:
                pass
            try:
                await client.block_user(uid)
            except:
                pass
            return

        # ara uyarı
        await event.reply(f"⚠️ Uyarı: ({info['count']}/{MAX_PM})")
