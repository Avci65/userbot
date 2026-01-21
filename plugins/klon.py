import os
import re
from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl import functions
from plugins._help import add_help

def setup(client):
    print("✅ klon.py plugin yüklendi")

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    def clean_invisible(text: str) -> str:
        if not text:
            return text
        # görünmez karakterleri temizle
        return re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]", "", text)

    async def get_full_user_from_event(event):
        # reply varsa
        if event.reply_to_msg_id:
            reply = await event.get_reply_message()
            try:
                if reply.forward and (reply.forward.from_id or reply.forward.channel_id):
                    uid = reply.forward.from_id or reply.forward.channel_id
                    return await client(GetFullUserRequest(uid))
                return await client(GetFullUserRequest(reply.sender_id))
            except Exception:
                return None

        # reply yoksa argüman
        parts = event.raw_text.split(maxsplit=1)
        if len(parts) < 2:
            return None
        query = parts[1].strip()

        try:
            entity = await client.get_entity(query)
            return await client(GetFullUserRequest(entity.id))
        except Exception:
            return None

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(klon)(?:\s|$)"))
    async def klon_handler(event):
        # Owner check
        if OWNER_ID != 0 and event.sender_id != OWNER_ID:
            return

        if event.fwd_from:
            return

        await event.edit("🧬 Klon hazırlanıyor...")

        replied_user = await get_full_user_from_event(event)
        if not replied_user:
            await event.edit("❌ Kullanıcı bulunamadı.\nKullanım: `.klon` (yanıtla) veya `.klon @username`")
            return

        user_id = replied_user.user.id

        # temp klasörü
        temp_dir = "./temp"
        os.makedirs(temp_dir, exist_ok=True)

        # profil foto indir (yoksa None döner)
        profile_pic = None
        try:
            profile_pic = await client.download_profile_photo(user_id, temp_dir)
        except:
            profile_pic = None

        # ad/soyad/bio
        first_name = clean_invisible(replied_user.user.first_name or "")[:64]
        last_name = replied_user.user.last_name
        if last_name is None:
            last_name = "⁪⁬⁮⁮⁮⁮ ‌‌‌‌"  # boş soyad trick
        last_name = clean_invisible(last_name)[:64]

        bio = clean_invisible(replied_user.about or "")[:70]

        # Profil güncelle
        try:
            await client(functions.account.UpdateProfileRequest(first_name=first_name))
            await client(functions.account.UpdateProfileRequest(last_name=last_name))
            await client(functions.account.UpdateProfileRequest(about=bio))
        except Exception as e:
            await event.edit(f"❌ Profil güncellenemedi:\n`{e}`")
            return

        # Foto varsa yükle
        if profile_pic:
            try:
                file = await client.upload_file(profile_pic)
                await client(functions.photos.UploadProfilePhotoRequest(file))
            except Exception:
                # foto yüklenemese bile devam
                pass

        await event.edit("✅ Klon tamamlandı 😈")

add_help(
    "klon",
    ".klon",
    "Yanıt verdiğin kişinin profilini (ad/soyad/bio/foto) klonlar. \nKullanım: `.klon` (reply) veya `.klon @username`"
)
