
# (c)@Merkurkedisi
"""Lütfen sadece .pinstall"""

from telethon import events

import asyncio

from events import register

@register(outgoing=True, pattern="^Sa$")

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

        await event.edit(animation_chars[i % 12])
