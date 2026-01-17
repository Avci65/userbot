import asyncio
from telethon import events

def setup(client):
    print("✅ sa.py plugin yüklendi")

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^sa$"))
    async def sa_handler(event):
        print("✅ SA komutu yakalandı")

        animation_interval = 0.4
        animation_chars = [
            "S",
            "SA",
            "SEA",
            "🌀Sea",
            "🍃Selam",
            "🔅Sa",
            "🍁Selammm",
            "🍃Naber",
            "🔅Ben Geldim",
            "**Hoşgeldim**",
            "**❄️Sea**"
        ]

        for ch in animation_chars:
            await event.edit(ch)
            await asyncio.sleep(animation_interval)
