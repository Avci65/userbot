import os
import asyncio
from telethon import events

def setup(client):
    print("✅ ig.py plugin yüklendi")

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(ig)\s*$"))
    async def ig_handler(event):
        if OWNER_ID != 0 and event.sender_id != OWNER_ID:
            return

        if event.fwd_from:
            return

        animation_interval = 0.5
        animation_chars = [
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️\n☁️🌙🌙☁️☁️🌙☁️☁️☁️",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n🌙🌙☁️✨☁️☁️☁️☁️☁️",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n🌙🌙☁️✨☁️☁️☁️☁️☁️\n🌙🌙☁️☁️☁️☁️☁️☁️☁️",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n🌙🌙☁️✨☁️☁️☁️☁️☁️\n🌙🌙☁️☁️☁️☁️☁️☁️☁️\n🌙🌙☁️☁️ İyi Geceler ✨",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n🌙🌙☁️✨☁️☁️☁️☁️☁️\n🌙🌙☁️☁️☁️☁️☁️☁️☁️\n🌙🌙☁️☁️ İyi Geceler ✨\n☁️🌙🌙☁️☁️🌙☁️☁️☁️",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n🌙🌙☁️✨☁️☁️☁️☁️☁️\n🌙🌙☁️☁️☁️☁️☁️☁️☁️\n🌙🌙☁️☁️ İyi Geceler ✨\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n☁️☁️🌙🌙🌙☁️☁️☁️☁️",
            "☁️☁️☁️☁️☁️☁️☁️☁️☁️\n🌟☁️🌙🌙🌙☁️☁️✨☁️\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n🌙🌙☁️✨☁️☁️☁️☁️☁️\n🌙🌙☁️☁️☁️☁️☁️☁️☁️\n🌙🌙☁️☁️ İyi Geceler ✨\n☁️🌙🌙☁️☁️🌙☁️☁️☁️\n☁️☁️🌙🌙🌙☁️☁️☁️☁️\n☁️☁️☁️☁️☁️☁️☁️☁️☁️",
        ]

        await event.edit("İyi Geceler")

        for ch in animation_chars:
            await asyncio.sleep(animation_interval)
            await event.edit(ch)
