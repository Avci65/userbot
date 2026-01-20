# plugins/translate.py
import requests
from telethon import events

# Basit Google translate endpoint (ücretsiz, key yok)
# Not: Bazen rate-limit olabilir. Olursa alternatif endpoint ekleriz.
GT_URL = "https://translate.googleapis.com/translate_a/single"

def _translate(text: str, target: str = "tr", source: str = "auto"):
    params = {
        "client": "gtx",
        "sl": source,
        "tl": target,
        "dt": "t",
        "q": text
    }
    r = requests.get(GT_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    # data[0] = [[translated, original, ...], ...]
    translated = "".join([x[0] for x in data[0] if x[0]])
    detected = data[2] if len(data) > 2 else source

    return translated, detected


def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(tr|translate)(?:\s+(\w+))?(?:\s+([\s\S]+))?$"))
    async def cmd_translate(event):
        """
        .tr en selam
        .tr tr hello
        reply + .tr en
        """
        replied = await event.get_reply_message()
        target = (event.pattern_match.group(2) or "").strip().lower()
        text = (event.pattern_match.group(3) or "").strip()

        if not target:
            target = "tr"  # default: TR

        if not text:
            if replied and replied.text:
                text = replied.text
            else:
                return await event.edit(
                    "❌ Kullanım:\n"
                    "`.tr en merhaba`\n"
                    "Reply + `.tr en`\n"
                    "Varsayılan: `.tr` = TR"
                )

        # çok uzun metinleri kes (Telegram edit limiti)
        if len(text) > 3500:
            text = text[:3500] + "..."

        await event.edit("🌍 Çeviriliyor...")

        try:
            translated, detected = _translate(text, target=target, source="auto")

            if not translated:
                return await event.edit("❌ Çeviri alınamadı.")

            # Output
            out = (
                f"🌍 **Translate**\n"
                f"**From:** `{detected}`\n"
                f"**To:** `{target}`\n\n"
                f"**Result:**\n{translated}"
            )

            # eğer edit limiti aşarsa mesaj at
            if len(out) > 4000:
                await event.delete()
                return await client.send_message(event.chat_id, out)

            await event.edit(out)

        except Exception as e:
            await event.edit(f"❌ Hata: `{str(e)}`")


    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(lang|langs|diller)\s*$"))
    async def cmd_lang(event):
        await event.edit(
            "🗣️ **Dil kodu örnekleri:**\n"
            "`tr` Türkçe\n"
            "`en` English\n"
            "`de` Deutsch\n"
            "`fr` Français\n"
            "`ru` Русский\n"
            "`ar` العربية\n"
            "`es` Español\n"
            "`it` Italiano\n"
            "`fa` فارسی\n\n"
            "Kullanım: `.tr en merhaba`"
        )
from plugins._help import add_help

add_help("translate", ".tr <hedef_dil> <metin> / reply + .tr <hedef_dil>", "Metni hedef dile çevirir. (Varsayılan hedef: tr)")
add_help("translate", ".translate <hedef_dil> <metin>", "(.tr ile aynı) Metni hedef dile çevirir.")
add_help("translate", ".lang / .langs / .diller", "Dil kodu örneklerini gösterir.")

