# plugins/emojify.py
import textwrap
from telethon import events

def setup(client):
    basemojitext = [
        "a","b","c","ç","d","e","f","g","ğ","h","i","j","k","l","m","n","o","ö",
        "p","q","r","s","t","u","ü","v","w","x","y","z","@",
        "0","1","2","3","4","5","6","7","8","9",
        " "
    ]

    # KISALTILMIŞ örnek emoji listesi (sende full liste var onu koyabilirsin)
    emojis = {
        "a": "🅰️",
        "b": "🅱️",
        "c": "🌜",
        "ç": "🌛",
        "d": "🌙",
        "e": "🎗️",
        "f": "🎏",
        "g": "🌀",
        "ğ": "🧿",
        "h": "♓",
        "i": "🎐",
        "j": "🎷",
        "k": "🎋",
        "l": "👢",
        "m": "〽️",
        "n": "🎵",
        "o": "🅾️",
        "ö": "⭕",
        "p": "🅿️",
        "q": "🍳",
        "r": "®️",
        "s": "💲",
        "t": "✝️",
        "u": "⛎",
        "ü": "🧉",
        "v": "✅",
        "w": "〰️",
        "x": "❌",
        "y": "🍸",
        "z": "💤",
        "@": "📧",
        "0":"0️⃣","1":"1️⃣","2":"2️⃣","3":"3️⃣","4":"4️⃣",
        "5":"5️⃣","6":"6️⃣","7":"7️⃣","8":"8️⃣","9":"9️⃣",
        " ": "   ",
    }

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(emoji)\s*(.*)$"))
    async def emojify_cmd(event):
        arg = (event.pattern_match.group(2) or "").strip()

        if not arg and event.is_reply:
            rep = await event.get_reply_message()
            arg = (rep.raw_text or "").strip()

        if not arg:
            return await event.edit("Kullanım: `.emoji selam` (veya mesaja reply + `.emoji`)")

        if len(arg) > 150:
            return await event.edit("❌ Çok uzun metin (max 150 karakter).")

        out = []
        for ch in arg.lower():
            out.append(emojis.get(ch, ch))

        await event.edit("".join(out))

    print("✅ emojify.py plugin yüklendi")
