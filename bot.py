import os
import textwrap
from io import BytesIO

import requests
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

# ---------------- QUATLY STYLE HELPERS ----------------
def _load_font(size: int, bold=False):
    try:
        if bold:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def _circle_crop(im: Image.Image, size: int):
    im = im.convert("RGBA").resize((size, size))
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out

def _gradient_bg(w, h):
    # Quatly benzeri koyu gradient
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(h):
        r = int(45 + (10 * y / h))
        g = int(30 + (10 * y / h))
        b = int(70 + (25 * y / h))
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))
    return img

async def make_quatly_sticker(replied_msg, out_path="quote.webp"):
    W, H = 512, 512
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    # Kart
    card = _gradient_bg(430, 260)
    card_x, card_y = 60, 150

    # Rounded card mask
    mask = Image.new("L", card.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, card.size[0], card.size[1]), radius=48, fill=255)
    base.paste(card, (card_x, card_y), mask)

    # Avatar (replied message sender)
    avatar_size = 110
    sender = await replied_msg.get_sender()

    pfp_io = BytesIO()
    downloaded = await client.download_profile_photo(sender, file=pfp_io)

    if downloaded:
        pfp_io.seek(0)
        avatar_img = Image.open(pfp_io)
    else:
        avatar_img = Image.new("RGB", (avatar_size, avatar_size), (90, 90, 90))

    avatar_img = _circle_crop(avatar_img, avatar_size)
    base.paste(avatar_img, (65, 70), avatar_img)

    # Text
    name = getattr(sender, "first_name", None) or "User"
    name_font = _load_font(56, bold=True)

    msg = (replied_msg.raw_text or "").strip()
    if len(msg) > 140:
        msg = msg[:140] + "…"

    msg_font = _load_font(44, bold=False)
    wrapped = "\n".join(textwrap.wrap(msg, width=14))

    # Draw name + message
    name_x = card_x + 30
    name_y = card_y + 35
    draw.text((name_x, name_y), name, font=name_font, fill=(255, 170, 60, 255))

    draw.multiline_text(
        (name_x, name_y + 85),
        wrapped,
        font=msg_font,
        fill=(255, 255, 255, 255),
        spacing=10
    )

    base.save(out_path, "WEBP", quality=95, method=6)

# ---------------- Commands ----------------
@client.on(events.NewMessage(pattern=r"(?i)^\.(ping)\s*$"))
async def cmd_ping(event):
    if not is_owner(event):
        return
    await event.reply("pong ✅")

@client.on(events.NewMessage(pattern=r"(?i)^\.(id)\s*$"))
async def cmd_id(event):
    await event.reply(f"🆔 ID: `{event.sender_id}`")

@client.on(events.NewMessage(pattern=r"(?i)^\.(q)\s*$"))
async def cmd_q(event):
    if not is_owner(event):
        return

    if not event.is_reply:
        return await event.reply("Bir mesaja yanıt verip `.q` yaz ✅")

    replied = await event.get_reply_message()
    msg = (replied.raw_text or "").strip()

    if not msg:
        return await event.reply("Bu mesajda metin yok 😅")

    await event.reply("✅ Sticker hazırlanıyor...")

    out_path = "quote.webp"
    await make_quatly_sticker(replied, out_path=out_path)
    await client.send_file(event.chat_id, out_path, force_document=False)

# ---------------- Start ----------------
client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
