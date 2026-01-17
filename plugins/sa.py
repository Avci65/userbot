import os
import asyncio
from telethon import events

def setup(client):
    print("✅ sa.py plugin yüklendi")

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^sa$"))
    async def sa_handler(event):
        if OWNER_ID != 0 and event.sender_id != OWNER_ID:
            return

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
