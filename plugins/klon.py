import os
import re
import json
from telethon import events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl import functions
from plugins._help import add_help


def setup(client):
    print("✅ klon.py plugin yüklendi")

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    # temp klasörü
    temp_dir = "./temp"
    os.makedirs(temp_dir, exist_ok=True)

    BACKUP_FILE = os.path.join(temp_dir, "unklon_backup.json")
    BACKUP_PHOTO = os.path.join(temp_dir, "unklon_photo.jpg")

    def clean_invisible(text: str) -> str:
        if not text:
            return text
        # görünmez karakterleri temizle
        return re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f]", "", text)

    def extract_user_obj(user_full):
        """
        Telethon sürümlerine göre UserFull içinden User nesnesini çeker.
        """
        if hasattr(user_full, "user") and user_full.user:
            return user_full.user
        if hasattr(user_full, "users") and user_full.users:
            return user_full.users[0]
        return None

    async def get_full_user_from_event(event):
        """
        Reply -> o kişiyi alır
        Reply yoksa -> .klon <username/id>
        """
        # reply varsa
        if event.reply_to_msg_id:
            reply = await event.get_reply_message()
            try:
                # forward mesajlarda forward sahibini al
                if reply.forward and (reply.forward.from_id or reply.forward.channel_id):
                    uid = reply.forward.from_id or reply.forward.channel_id
                    return await client(GetFullUserRequest(uid))
                return await client(GetFullUserRequest(reply.sender_id))
            except Exception as e:
                print("⚠️ get_full_user reply error:", e)
                return None

        # reply yoksa argüman al
        parts = event.raw_text.split(maxsplit=1)
        if len(parts) < 2:
            return None
        query = parts[1].strip()

        try:
            entity = await client.get_entity(query)
            return await client(GetFullUserRequest(entity.id))
        except Exception as e:
            print("⚠️ get_full_user entity error:", e)
            return None

    async def backup_my_profile():
        """
        Unklon için kendi profilini yedekler.
        (ad/soyad/bio + profil foto)
        """
        try:
            me_full = await client(GetFullUserRequest("me"))
            me_user = extract_user_obj(me_full)
            if not me_user:
                return False, "User obj alınamadı"

            first_name = me_user.first_name or ""
            last_name = me_user.last_name or ""
            bio = getattr(me_full, "about", "") or ""

            # profil foto indir
            my_photo = None
            try:
                my_photo = await client.download_profile_photo("me", file=BACKUP_PHOTO)
            except Exception as e:
                print("⚠️ Backup foto indirilemedi:", e)
                my_photo = None

            # gerçekten dosya var mı?
            has_photo = False
            if my_photo and os.path.exists(my_photo):
                has_photo = True

            data = {
                "first_name": first_name,
                "last_name": last_name,
                "bio": bio,
                "has_photo": has_photo
            }

            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True, None

        except Exception as e:
            return False, str(e)

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(klon)(?:\s|$)"))
    async def klon_handler(event):
        # Owner check
        if OWNER_ID != 0 and event.sender_id != OWNER_ID:
            return
        if event.fwd_from:
            return

        await event.edit("🧬 Klon hazırlanıyor...")

        # ✅ önce backup al
        ok, err = await backup_my_profile()
        if ok:
            print("✅ UnKlon backup alındı.")
        else:
            print("⚠️ Backup alınamadı:", err)

        replied_user = await get_full_user_from_event(event)
        if not replied_user:
            await event.edit("❌ Kullanıcı bulunamadı.\nKullanım: `.klon` (reply) veya `.klon @username`")
            return

        user_obj = extract_user_obj(replied_user)
        if not user_obj:
            await event.edit("❌ Kullanıcı datası çekilemedi (telethon uyumsuzluğu).")
            return

        user_id = user_obj.id

        # Profil foto indir
        profile_pic = None
        try:
            profile_pic = await client.download_profile_photo(user_id, file=temp_dir)
        except Exception as e:
            print("⚠️ Klon foto indirilemedi:", e)
            profile_pic = None

        if profile_pic and not os.path.exists(profile_pic):
            profile_pic = None

        # ad/soyad/bio
        first_name = clean_invisible(user_obj.first_name or "")[:64]

        last_name = user_obj.last_name
        if last_name is None:
            last_name = "⁪⁬⁮⁮⁮⁮ ‌‌‌‌"  # boş soyad trick
        last_name = clean_invisible(last_name)[:64]

        bio = clean_invisible(getattr(replied_user, "about", "") or "")[:70]

        # Profil güncelle
        try:
            await client(functions.account.UpdateProfileRequest(first_name=first_name))
            await client(functions.account.UpdateProfileRequest(last_name=last_name))
            await client(functions.account.UpdateProfileRequest(about=bio))
        except Exception as e:
            await event.edit(f"❌ Profil güncellenemedi:\n`{e}`")
            return

        # ✅ Foto varsa yükle (en sağlam yöntem)
        if profile_pic:
            try:
                await client.upload_profile_photo(profile_pic)
                print("✅ Klon profil foto güncellendi.")
            except Exception as e:
                print("⚠️ Klon profil foto yüklenemedi:", e)

        await event.edit("✅ Klon tamamlandı 😈\n`Geri almak için: .unklon`")

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(unklon)\s*$"))
    async def unklon_handler(event):
        # Owner check
        if OWNER_ID != 0 and event.sender_id != OWNER_ID:
            return
        if event.fwd_from:
            return

        if not os.path.exists(BACKUP_FILE):
            await event.edit("❌ Backup bulunamadı.\nÖnce `.klon` kullanmalısın.")
            return

        await event.edit("♻️ Eski profil geri yükleniyor...")

        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            bio = data.get("bio", "")
            has_photo = data.get("has_photo", False)

            # profil bilgilerini geri yükle
            await client(functions.account.UpdateProfileRequest(first_name=first_name))
            await client(functions.account.UpdateProfileRequest(last_name=last_name))
            await client(functions.account.UpdateProfileRequest(about=bio))

            # ✅ Foto varsa geri yükle (en sağlam yöntem)
            if has_photo and os.path.exists(BACKUP_PHOTO):
                try:
                    await client.upload_profile_photo(BACKUP_PHOTO)
                    print("✅ UnKlon profil foto geri yüklendi.")
                except Exception as e:
                    print("⚠️ UnKlon foto yüklenemedi:", e)

            await event.edit("✅ Profil geri yüklendi! (UnKlon başarılı)")

        except Exception as e:
            await event.edit(f"❌ UnKlon başarısız:\n`{e}`")

    # Help entegrasyonu
    add_help(
        "klon",
        ".klon / .unklon",
        "Klon: Yanıt verdiğin kişinin profilini (ad/soyad/bio/foto) klonlar.\n"
        "UnKlon: Klon öncesi profiline geri döner.\n\n"
        "Kullanım:\n"
        "`.klon` (reply) veya `.klon @username`\n"
        "`.unklon`"
    )
