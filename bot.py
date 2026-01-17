import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import textwrap
from PIL import Image, ImageDraw, ImageFont

print("API_ID ENV RAW:", repr(os.getenv("API_ID")))
print("API_HASH ENV RAW:", repr(os.getenv("API_HASH")))
print("SESSION ENV RAW:", repr(os.getenv("SESSION_STRING"))[:60])

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_STRING = os.getenv("SESSION_STRING", "")
SESSION_STRING = SESSION_STRING.replace("\n", "").replace("\r", "").strip()

print("API_ID:", API_ID)
print("HASH_LEN:", len(API_HASH))
print("SESSION_LEN:", len(SESSION_STRING))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

def is_owner(event):
    return OWNER_ID == 0 or event.sender_id == OWNER_ID


if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(pattern=r"\.ping"))
async def ping(event):
    if not is_owner(event):
        return
    await event.reply("pong ✅")

client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
def make_quote_sticker(text: str, out_path="quote.webp"):
    # Yazıyı temizle
    text = (text or "").strip()
    if not text:
        text = "..."

    # Çok uzunsa kısalt
    if len(text) > 700:
        text = text[:700] + "…"

    # Sticker boyutu
    W, H = 512, 512
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Arka plan (hafif yuvarlatılmış kutu)
    pad = 40
    box = (pad, pad, W - pad, H - pad)
    draw.rounded_rectangle(box, radius=40, fill=(20, 20, 20, 230))

    # Font (Railway’de font yolu değişebilir)
    # Varsayılan fontla da çalışır
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 36)
    except:
        font = ImageFont.load_default()

    # Metni satırlara böl
    wrapped = "\n".join(textwrap.wrap(text, width=22))

    # Metni ortala
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W - tw) // 2
    y = (H - th) // 2

    draw.multiline_text((x, y), wrapped, font=font, fill=(255, 255, 255, 255), spacing=8, align="center")

    # WebP kaydet (sticker format)
    img.save(out_path, "WEBP", quality=95, method=6)

@client.on(events.NewMessage(pattern=r"\.q$"))
async def quote_sticker(event):
    # sadece reply ile çalışsın
    if not event.is_reply:
        return await event.reply("Bir mesaja yanıt verip `.q` yaz ✅")

    replied = await event.get_reply_message()

    # Metin al
    text = replied.raw_text or ""
    if not text.strip():
        return await event.reply("Bu mesajda metin yok 😅")

    out_path = "quote.webp"
    make_quote_sticker(text, out_path=out_path)

    # Sticker olarak gönder
    await client.send_file(event.chat_id, out_path, force_document=False)
