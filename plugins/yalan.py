# plugins/yalan.py
from telethon import events
import asyncio

def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(yalan)\s*$"))
    async def cmd_yalan(event):
        if event.fwd_from:
            return

        animation_interval = 2.5
        animation_chars = [
            "`Yalan yükleniyor... %1`\n**█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒**",
            "`Yalan yükleniyor... 17%`\n**████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒**",
            "`Yalan bulunuyor... 28%`\n**██████▒▒▒▒▒▒▒▒▒▒▒▒▒▒**",
            "`Yalan bulunuyor... 39%`\n**████████▒▒▒▒▒▒▒▒▒▒▒▒**",
            "`Yalan deneniyor... 51%`\n**██████████▒▒▒▒▒▒▒▒▒▒**",
            "`Yalan deneniyor... 67%`\n**████████████▒▒▒▒▒▒▒▒**",
            "`İnandırıcılık yetersiz... 72%`\n**█████████████▒▒▒▒▒▒▒**",
            "`İnandırıcılık yetersiz... 83%`\n**███████████████▒▒▒▒▒**",
            "`Yalan bulunamadı :( 87%`\n**█████████████████▒▒▒**",
            "`Yalan bulunamadı :( 91%`\n**██████████████████▒▒**",
            "`Başaramadık abi :( 100%`\n**████████████████████**",
        ]

        # ilk mesaj
        await event.edit("`Yalan hazırlanıyor...`")

        for frame in animation_chars:
            await asyncio.sleep(animation_interval)
            await event.edit(frame)


# HELP entegrasyonu (purge örneğindeki gibi)
from plugins._help import add_help
add_help(
    "yalan",
    ".yalan\nYalan animasyonu gönderir."
)
