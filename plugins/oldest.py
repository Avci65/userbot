# plugins/oldest.py
from telethon import events


def build_msg_link(chat, msg_id: int) -> str:
    # public group/channel
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{msg_id}"

    cid = getattr(chat, "id", None)
    if cid is None:
        return ""

    cid_str = str(cid)
    if cid_str.startswith("-100"):
        internal = cid_str[4:]  # -100'ü at
        return f"https://t.me/c/{internal}/{msg_id}"

    internal = str(abs(cid))
    return f"https://t.me/c/{internal}/{msg_id}"


def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(oldest)(?:\s+(dm))?\s*$"))
    async def cmd_oldest(event):
        if not event.is_group:
            return await event.edit("❌ `.oldest` sadece gruplarda çalışır.")

        dm_mode = bool(event.pattern_match.group(2))  # dm yazıldı mı?

        # ✅ DM moduysa komutu hemen sil
        if dm_mode:
            try:
                await event.delete()
            except:
                pass
        else:
            await event.edit("🔎 En eski mesaj aranıyor...")

        try:
            oldest = None

            # en eski erişilebilir mesajı bul
            async for msg in client.iter_messages(event.chat_id, reverse=True):
                if msg:
                    oldest = msg
                    break

            if not oldest:
                if dm_mode:
                    return await client.send_message("me", "❌ En eski mesaj bulunamadı (erişim kısıtlı olabilir).")
                return await event.edit("❌ En eski mesaj bulunamadı (erişim kısıtlı olabilir).")

            chat = await event.get_chat()
            link = build_msg_link(chat, oldest.id)

            # kullanıcı bilgisi
            user_name = f"{oldest.sender_id}"
            user_tag = f"`{oldest.sender_id}`"
            try:
                ent = await client.get_entity(oldest.sender_id)
                first = getattr(ent, "first_name", None) or "User"
                username = getattr(ent, "username", None)

                user_name = first
                if username:
                    user_tag = f"[{first}](tg://user?id={oldest.sender_id}) (@{username})"
                else:
                    user_tag = f"[{first}](tg://user?id={oldest.sender_id})"
            except:
                pass

            # mesaj preview
            text_preview = (oldest.raw_text or "").strip()
            if len(text_preview) > 200:
                text_preview = text_preview[:200] + "..."

            out = (
                f"📜 **EN ESKİ MESAJ (Grup: {getattr(chat, 'title', 'Group')})**\n\n"
                f"👤 **Gönderen:** {user_tag}\n"
                f"🆔 **Mesaj ID:** `{oldest.id}`\n"
                f"📅 **Tarih:** `{oldest.date}`\n"
                f"🔗 **Link:** {link if link else '`link üretilemedi`'}\n\n"
                f"💬 **İçerik:** `{text_preview if text_preview else '—'}`"
            )

            # ✅ DM modu: sadece DM'ye at
            if dm_mode:
                return await client.send_message("me", out)

            # normal mod: gruba yaz
            await event.edit(out)

        except Exception as e:
            if dm_mode:
                await client.send_message("me", f"❌ Hata: `{str(e)}`")
            else:
                await event.edit(f"❌ Hata: `{str(e)}`")


# ---- HELP ----
from plugins._help import add_help
add_help("tools", ".oldest", "Gruptaki en eski mesajı bulur ve linkini verir.")
add_help("tools", ".oldest dm", "Komutu siler, sonucu sadece sana DM (Saved Messages) olarak atar.")
