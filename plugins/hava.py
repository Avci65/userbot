# plugins/hava.py
import os
import requests
from telethon import events

def setup(client):
    API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not API_KEY:
        print("⚠️ hava.py: OPENWEATHER_API_KEY yok, hava sistemi çalışmayacak.")
        return

    def get_weather(city: str):
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric",   # Celsius
            "lang": "tr"         # Türkçe açıklama
        }

        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(hava)(?:\s+(.+))?\s*$"))
    async def cmd_hava(event):
        city = (event.pattern_match.group(2) or "").strip()

        if not city:
            return await event.edit("❌ Kullanım: `.hava <şehir>`\nÖrn: `.hava istanbul`")

        await event.edit("🌤️ Hava durumu alınıyor...")

        try:
            data = get_weather(city)

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

        except requests.exceptions.HTTPError:
            # genelde city bulunamadı
            await event.edit("❌ Şehir bulunamadı. Örn: `.hava istanbul`")
        except Exception as e:
            await event.edit(f"❌ Hata: `{str(e)}`")


# ---- HELP ----
from plugins._help import add_help
add_help("hava", ".hava <şehir>", "Güncel hava durumunu gösterir. Örn: `.hava istanbul`")
