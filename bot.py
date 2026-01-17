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

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

def is_owner(event) -> bool:
    return OWNER_ID == 0 or event.sender_id == OWNER_ID

if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ---------------- FONT ----------------
def _load_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

# ---------------- Sticker Generator (Quatly Style) ----------------
def make_quote_sticker(text: str, out_path="quote.webp"):
    text = (text or "").strip() or "..."
    if len(text) > 800:
        text = text[:800] + "…"

    W, H = 512, 512
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # şeffaf arka plan
    draw = ImageDraw.Draw(img)

    wrapped = "\n".join(textwrap.wrap(text, width=20))

    font_size = 72
    font = _load_font(font_size)

    while font_size > 20:
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=10)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        if tw <= 420 and th <= 360:
            break

        font_size -= 4
        font = _load_font(font_size)

    pad_x, pad_y = 36, 30
    box_w = min(460, tw + pad_x * 2)
    box_h = min(420, th + pad_y * 2)

    x1 = (W - box_w) // 2
    y1 = (H - box_h) // 2
    x2 = x1 + box_w
    y2 = y1 + box_h

    draw.rounded_rectangle((x1, y1, x2, y2), radius=42, fill=(255, 255, 255, 235))
    draw.rounded_rectangle((x1+2, y1+2, x2+2, y2+2), radius=42, outline=(0, 0, 0, 25), width=2)

    text_x = (W - tw) // 2
    text_y = (H - th) // 2

    draw.multiline_text((text_x, text_y), wrapped, font=font, fill=(0, 0, 0, 255),
                        spacing=10, align="center")

    img.save(out_path, "WEBP", quality=95, method=6)

# ---------------- Commands ----------------
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
