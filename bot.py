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
    return OWNER_ID == 0 or event.sender_id == OWNER_ID


if API_ID == 0 or not API_HASH or not SESSION_STRING:
    raise ValueError("API_ID / API_HASH / SESSION_STRING ortam değişkenleri eksik!")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
def _load_font(size: int):
    # Railway'de genelde DejaVuSans bulunur
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()
# ---------------- Sticker Generator ----------------
def make_quote_sticker(text: str, out_path="quote.webp"):
    text = (text or "").strip() or "..."
    if len(text) > 800:
        text = text[:800] + "…"

    W, H = 512, 512
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # ✅ tamamen şeffaf arka plan
    draw = ImageDraw.Draw(img)

    # Metni satırlara böl (kısa metinler daha az satır)
    # width değeri satır uzunluğunu belirler
    wrapped = "\n".join(textwrap.wrap(text, width=20))

    # ✅ Otomatik font büyüklüğü: metin sığana kadar küçült
    font_size = 72  # başlangıç büyük
    font = _load_font(font_size)

    while font_size > 20:
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=10)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # metin alanı
        max_w = 420
        max_h = 360
        if tw <= max_w and th <= max_h:
            break

        font_size -= 4
        font = _load_font(font_size)

    # Balon ölçüsü
    pad_x, pad_y = 36, 30
    box_w = min(460, tw + pad_x * 2)
    box_h = min(420, th + pad_y * 2)

    x1 = (W - box_w) // 2
    y1 = (H - box_h) // 2
    x2 = x1 + box_w
    y2 = y1 + box_h

    # ✅ Quatly benzeri açık balon
    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=42,
        fill=(255, 255, 255, 235)  # beyaz balon
    )

    # balon gölgesi efekti (hafif)
    draw.rounded_rectangle(
        (x1+2, y1+2, x2+2, y2+2),
        radius=42,
        outline=(0, 0, 0, 25),
        width=2
    )

    # Metin ortalama
    text_x = (W - tw) // 2
    text_y = (H - th) // 2

    # ✅ siyah metin
    draw.multiline_text(
        (text_x, text_y),
        wrapped,
        font=font,
        fill=(0, 0, 0, 255),
        spacing=10,
        align="center"
    )

    img.save(out_path, "WEBP", quality=95, method=6)

# ---------------- Start ----------------
client.start()
print("✅ Userbot başladı")
client.run_until_disconnected()
