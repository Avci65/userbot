# plugins/hava.py
import os
import requests
from telethon import events

def setup(client):
    API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
    print("✅ OPENWEATHER_API_KEY:", API_KEY[:6], "len=", len(API_KEY))

    if not API_KEY:
        print("⚠️ hava.py: OPENWEATHER_API_KEY yok, hava sistemi çalışmayacak.")
        return

    def normalize_city(s: str) -> str:
        # Türkçe karakterleri normalize et (İ -> I, ş -> s vs.)
        tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        return s.translate(tr_map).strip()

    def get_weather(city: str):
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric",   # Celsius
            "lang": "tr"         # Türkçe açıklama
        }
        r = requests.get(url, params=params, timeout=20)
        return r

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(hava)(?:\s+(.+))?\s*$"))
    async def cmd_hava(event):
        city = (event.pattern_match.group(2) or "").strip()
        if not city:
            return await event.edit("❌ Kullanım: `.hava <şehir>`\nÖrn: `.hava istanbul`")

        # normalize + ülke ekle
        city = normalize_city(city)
        if "," not in city:
            city = f"{city},tr"   # ✅ default TR

        await event.edit("🌤️ Hava durumu alınıyor...")

        try:
            r = get_weather(city)

            # HTTP hata ayrımı
            if r.status_code == 401:
                return await event.edit("❌ API Key hatalı / aktif değil. (401 Unauthorized)\nRailway Variables'a doğru eklediğine emin ol.")
            if r.status_code == 429:
                return await event.edit("⚠️ Çok fazla istek atıldı. (429 Rate limit)\nBiraz bekleyip tekrar dene.")
            if r.status_code == 404:
                return await event.edit("❌ Şehir bulunamadı. Örn: `.hava istanbul` veya `.hava istanbul,tr`")

            r.raise_for_status()
            data = r.json()

            name = data.get("name", city)
            country = data.get("sys", {}).get("country", "")
            w = data["weather"][0]
            main = data["main"]
            wind = data.get("wind", {})

            desc = w.get("description", "-")
            temp = main.get("temp", "-")
            feels = main.get("feels_like", "-")
            hum = main.get("humidity", "-")
            press = main.get("pressure", "-")
            wind_speed = wind.get("speed", "-")

            out = (
                f"🌍 **Hava Durumu**\n"
                f"📍 **Konum:** `{name}` {f'({country})' if country else ''}\n"
                f"🌤️ **Durum:** `{desc}`\n\n"
                f"🌡️ **Sıcaklık:** `{temp}°C`\n"
                f"🥶 **Hissedilen:** `{feels}°C`\n"
                f"💧 **Nem:** `{hum}%`\n"
                f"🔽 **Basınç:** `{press} hPa`\n"
                f"🌬️ **Rüzgar:** `{wind_speed} m/s`"
            )

            await event.edit(out)

        except Exception as e:
            await event.edit(f"❌ Hata: `{str(e)}`")


# ---- HELP ----
from plugins._help import add_help
add_help("hava", ".hava <şehir>", "Güncel hava durumunu gösterir. Örn: `.hava istanbul`")
