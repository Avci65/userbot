import os
import textwrap
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from PIL import Image, ImageDraw, ImageFont

# ---------------- ENV ----------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_STRING = os.getenv("SESSION_STRING", "")
SESSION_STRING = SESSION_STRING.replace("\n", "").replace("\r", "").strip()

OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Railway Variables'a eklenecek

def is_owner(event) -> bool:
    return OWNER_ID != 0 and event.sender_id == OWNER_ID

if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------------- Sticker Generator ----------------
def make_quote_sticker(text: str, out_path="quote.webp"):
    text = (text or "").strip() or "..."
    if len(text) > 700:
        text = text[:700] + "…"

    W, H = 512, 512
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = 40
    box = (pad, pad, W - pad, H - pad)
    draw.rounded_rectangle(box, radius=40, fill=(20, 20, 20, 230))

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 36)
    except:
        font = ImageFont.load_default()

    wrapped = "\n".join(textwrap.wrap(text, width=22))

    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W - tw) // 2
    y = (H - th) // 2

    draw.multiline_text(
        (x, y),
        wrapped,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=8,
        align="center",
    )

    img.save(out_path, "WEBP", quality=95, method=6)

# ---------------- Commands ----------------
@client.on(events.NewMessage(pattern=r"(?i)^\.(id)\s*$"))
async def cmd_id(event):
    # İstersen bunu da owner-only yapabiliriz ama genelde 1 kere lazım.
    await event.reply(f"🆔 ID: `{event.sender_id}`")

@client.on(events.NewMessage(pattern=r"(?i)^\.(ping)\s*$"))
async def cmd_ping(event):
    if not is_owner(event):
        return
    await event.reply("pong ✅")

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

    await event.reply("✅ Sticker hazırlanıyor...")

    out_path = "quote.webp"
    make_quote_sticker(text, out_path=out_path)
    await client.send_file(event.chat_id, out_path, force_document=False)

# ---------------- Start ----------------
client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
