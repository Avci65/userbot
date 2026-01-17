import asyncio
from telethon import events

async def merkurkedissa(event):

    if event.fwd_from:
        return

    animation_interval = 0.4
    animation_ttl = range(0, 12)

    await event.edit("Selamün Aleyküm..🐺")

    animation_chars = [
        "S",
        "SA",
        "SEA",
        "**Selam Almayanın Mq**",
        "🌀Sea",
        "🍃Selam",
        "🔅Sa",
        "🍁Selammm",
        "🍃Naber",
        "🔅Ben Geldim",
        "**Hoşgeldim**",
        "**❄️Sea**"
    ]

    for i in animation_ttl:
        await asyncio.sleep(animation_interval)
        await event.edit(animation_chars[i])

def setup(client):
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^sa$"))
    async def handler(event):
        await merkurkedissa(event)
