# plugins/hack.py
from telethon import events
import asyncio


def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(hack)\s*$"))
    async def cmd_hack(event):
        animation_interval = 3
        animation_chars = [
            "`Connecting To Hacked Private Server...`",
            "`Target Selected.`",
            "`Hacking... 0%\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 4%\n█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 8%\n██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 20%\n█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 36%\n█████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 52%\n█████████████▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 84%\n█████████████████████▒▒▒▒ `",
            "`Hacking... 100%\n█████████HACKED███████████ `",
            "`Targeted Account Hacked...\n\nPay 69$ To Remove this hack..`"
        ]

        await event.edit("Hacking..")
        for frame in animation_chars:
            await asyncio.sleep(animation_interval)
            await event.edit(frame)


    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(hack2)\s*$"))
    async def cmd_hack2(event):
        animation_interval = 2
        animation_chars = [
            "`Programlar hazır !`",
            "`İşlem başlatılıyor \n(0%) ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`Sistem özellikleri alınıyor. \n(5%) █▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`Sistem özellikleri alınıyor.. \n(10%) ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`Sistem özellikleri alınıyor... \n(15%) ███▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`Betik yürütülüyor. \n(20%) ████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`Betik yürütülüyor.. \n(25%) █████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`Betik yürütülüyor... \n(30%) ██████▒▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`IP adresi alınıyor. \n(35%) ███████▒▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`IP adresi alınıyor.. \n(40%) ████████▒▒▒▒▒▒▒▒▒▒▒▒`",
            "`IP adresi alınıyor... \n(45%) █████████▒▒▒▒▒▒▒▒▒▒▒`",
            "`MAC adresi alınıyor. \n(50%) ██████████▒▒▒▒▒▒▒▒▒▒`",
            "`MAC adresi alınıyor.. \n(55%) ███████████▒▒▒▒▒▒▒▒▒`",
            "`MAC adresi alınıyor... \n(60%) ████████████▒▒▒▒▒▒▒▒`",
            "`Dosyalar yükleniyor. \n(65%) █████████████▒▒▒▒▒▒▒`",
            "`Dosyalar yükleniyor.. \n(70%) ██████████████▒▒▒▒▒▒`",
            "`Dosyalar yükleniyor... \n(75%) ███████████████▒▒▒▒▒`",
            "`Dosyalar yükleniyor. \n(80%) ████████████████▒▒▒▒`",
            "`Dosyalar yükleniyor.. \n(85%) █████████████████▒▒▒`",
            "`Dosyalar yükleniyor... \n(90%) ██████████████████▒▒`",
            "`Dosyalar yükleniyor. \n(95%) ███████████████████▒`",
            "`Temizleniyor.. \n(100%) ███████████████████`",
            "`İşlem Tamam... \n(100%) ███████████████████ `",
            "`Bilgisayar tarafımızca hacklendi.\nHack'i kaldırmak için 100$ ödeyin`"
        ]

        await event.edit("`Hazırlık sürüyor...`")
        for frame in animation_chars:
            await asyncio.sleep(animation_interval)
            await event.edit(frame)


    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(hekir)\s*$"))
    async def cmd_hekir(event):
        animation_interval = 3
        animation_chars = [
            "`Yine Aşık ettin Kendine Zalımın Kızı...`",
            "`Hazırım.`",
            "`Aha Şimdi Sıçtın... 0%\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 4%\n█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 8%\n██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 20%\n█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 36%\n█████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 52%\n█████████████▒▒▒▒▒▒▒▒▒▒▒▒ `",
            "`Hacking... 84%\n█████████████████████▒▒▒▒ `",
            "`Hacking... 100%\n█████████HACKED███████████ `",
            "`Girdim Sanki...\n\n Para ödemene gerek yok seni almışım yeter..`"
        ]

        await event.edit("Kalbine giriyorum..")
        for frame in animation_chars:
            await asyncio.sleep(animation_interval)
            await event.edit(frame)


# ---- HELP ----
from plugins._help import add_help
add_help("eğlence", ".hack", "Sahte hack animasyonu (eğlence).")
add_help("eğlence", ".hack2", "Gelişmiş sahte hack animasyonu.")
add_help("eğlence", ".hekir", "Romantik sahte hack animasyonu 😄")
