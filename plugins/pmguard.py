# plugins/pmguard.py
import time
from telethon import events

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

    async def _resolve_target_user(event):
        """
        Kullanıcı çözümleme:
        1) Reply varsa replied.sender_id
        2) Komut parametresi varsa @username / id ile çöz
        """
        replied = await event.get_reply_message()
        if replied and replied.sender_id:
            return replied.sender_id

        # komuttan sonra argüman
        arg = (event.pattern_match.group(2) or "").strip()
        if not arg:
            return None

        # @username veya id
        try:
            ent = await client.get_entity(arg)
            return ent.id
        except:
            return None

    async def _get_name(uid: int) -> str:
        try:
            ent = await client.get_entity(uid)
            return (getattr(ent, "first_name", None) or getattr(ent, "title", None) or "User")
        except:
            return "User"

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
    # .allow  (DM + Grup)
    # - reply ile
    # - veya .allow @username / .allow 12345
    # ---------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(allow)(?:\s+(.+))?\s*$"))
    async def cmd_allow(event):
        uid = await _resolve_target_user(event)
        if not uid:
            return await event.edit(
                "❌ Kullanım:\n"
                "Reply + `.allow`\n"
                "`.allow @kullaniciadi`\n"
                "`.allow user_id`"
            )

        _allow_user(uid)
        name = await _get_name(uid)
        await event.edit(f"✅ `{name}` izinlilere eklendi. (whitelist)")

    # ---------------------------
    # .block  (DM + Grup)
    # - reply ile
    # - veya .block @username / .block 12345
    # ---------------------------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(block)(?:\s+(.+))?\s*$"))
    async def cmd_block(event):
        uid = await _resolve_target_user(event)
        if not uid:
            return await event.edit(
                "❌ Kullanım:\n"
                "Reply + `.block`\n"
                "`.block @kullaniciadi`\n"
                "`.block user_id`"
            )

        # whitelistten çıkar
        _disallow_user(uid)

        try:
            await client.block_user(uid)
        except Exception as e:
            return await event.edit(f"❌ Block başarısız: `{str(e)}`")

        name = await _get_name(uid)
        await event.edit(f"⛔ `{name}` blocklandı.")

    # ---------------------------
    # PM Guard Listener (incoming)
    # ---------------------------
    @client.on(events.NewMessage(incoming=True))
    async def pmguard_listener(event):
        # sadece özel mesajlar
        if not event.is_private:
            return

        uid = event.sender_id
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


# ---- HELP ----
from plugins._help import add_help
add_help("pmguard", ".pmguard on/off", "PM Guard aç/kapat (DM spam engelleme)")
add_help("pmguard", ".allow (reply/@user/id)", "Kullanıcıyı whitelist'e ekler (grup veya DM)")
add_help("pmguard", ".block (reply/@user/id)", "Kullanıcıyı whitelistten çıkarır ve blocklar (grup veya DM)")
