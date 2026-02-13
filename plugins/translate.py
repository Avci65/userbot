import requests
from telethon import events

# ücretsiz Google translate endpoint
TRANS_API = "https://translate.googleapis.com/translate_a/single"


def translate_text(text: str, target: str) -> str:
    try:
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target,
            "dt": "t",
            "q": text,
        }
        r = requests.get(TRANS_API, params=params, timeout=20).json()
        return "".join(part[0] for part in r[0])
    except Exception:
        return text


def setup(client, rdb, is_owner):
    """
    Global translate mode

    .dil ing      -> aç
    .dil kapat    -> kapat
    """

    KEY = "translate:mode"

    # ---------- MODE SET ----------
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.dil\s+(.+)$"))
    async def cmd_dil(event):
        if not is_owner(event):
            return

        if not rdb:
            return await event.reply("❌ Redis yok!")

        arg = event.pattern_match.group(1).strip().lower()

        if arg in ("kapat", "off", "stop"):
            rdb.delete(KEY)
            return await event.reply("🛑 Translate kapatıldı.")

        # dil kaydet
        rdb.set(KEY, arg)
        await event.reply(f"🌍 Translate açıldı → `{arg}`")

    # ---------- AUTO TRANSLATE ----------
    @client.on(events.NewMessage(outgoing=True))
    async def auto_translate(event):
        if not rdb:
            return

        lang = rdb.get(KEY)
        if not lang:
            return

        # komutları çevirme
        if not event.raw_text:
            return

        text = event.raw_text.strip()

        if not text:
            return

        if text.startswith("."):
            return

        # zaten çevrilmişse loop olmasın
        if getattr(event, "_translated", False):
            return

        translated = translate_text(text, lang)

        if not translated or translated == text:
            return

        try:
            await event.edit(translated)
            event._translated = True
        except Exception:
            pass

    print("✅ translate.py plugin yüklendi")
