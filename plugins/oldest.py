# plugins/oldest.py
from telethon import events
from telethon.errors import RPCError


def build_msg_link(chat, msg_id: int) -> str:
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{msg_id}"

    cid = getattr(chat, "id", None)
    if cid is None:
        return ""

    cid_str = str(cid)
    if cid_str.startswith("-100"):
        internal = cid_str[4:]
        return f"https://t.me/c/{internal}/{msg_id}"

    internal = str(abs(cid))
    return f"https://t.me/c/{internal}/{msg_id}"


async def message_exists(client, chat_id: int, msg_id: int):
    """
    Bu msg_id gerçekten var mı? (silinmiş olabilir)
    """
    try:
        m = await client.get_messages(chat_id, ids=msg_id)
        if not m:
            return None
        # Telethon bazen MessageEmpty döndürebilir
        if getattr(m, "id", None) != msg_id:
            return None
        # mesaj var ama boş olabilir
        return m
    except RPCError:
        return None
    except Exception:
        return None


async def find_oldest_message(client, chat_id: int, last_id: int):
    """
    Binary search ile en küçük var olan msg_id bulunur.
    """
    lo, hi = 1, last_id
    best = None

    while lo <= hi:
        mid = (lo + hi) // 2
        m = await message_exists(client, chat_id, mid)

        if m:
            best = m
            hi = mid - 1  # daha eski var mı?
        else:
            lo = mid + 1  # bu id yok -> daha ileri bak

    # best bulunduysa onu döndür, yoksa None
    return best


def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(oldest)(?:\s+(dm))?\s*$"))
    async def cmd_oldest(event):
        if not event.is_group:
            return await event.edit("❌ `.oldest` sadece gruplarda çalışır.")

        dm_mode = bool(event.pattern_match.group(2))

        # DM modu: komutu sil
        if dm_mode:
            try:
                await event.delete()
            except:
                pass
        else:
            await event.edit("🔎 En eski mesaj aranıyor (binary search)...")

        try:
            # en son mesajı al → last_id
            last = await client.get_messages(event.chat_id, limit=1)
            if not last:
                msg = "❌ Bu sohbette mesaj yok gibi görünüyor."
                if dm_mode:
                    return await client.send_message("me", msg)
                return await event.edit(msg)

            last_id = last[0].id

            # en eski erişilebilir mesajı bul
            oldest = await find_oldest_message(client, event.chat_id, last_id)

            if not oldest:
                msg = "❌ En eski mesaj bulunamadı (çok fazla silinmiş olabilir)."
                if dm_mode:
                    return await client.send_message("me", msg)
                return await event.edit(msg)

            chat = await event.get_chat()
            link = build_msg_link(chat, oldest.id)

            # kullanıcı bilgisi
            user_tag = f"`{oldest.sender_id}`"
            try:
                ent = await client.get_entity(oldest.sender_id)
                first = getattr(ent, "first_name", None) or "User"
                username = getattr(ent, "username", None)
                if username:
                    user_tag = f"[{first}](tg://user?id={oldest.sender_id}) (@{username})"
                else:
                    user_tag = f"[{first}](tg://user?id={oldest.sender_id})"
            except:
                pass

            text_preview = (oldest.raw_text or "").strip()
            if len(text_preview) > 200:
                text_preview = text_preview[:200] + "..."

            out = (
                f"📜 **EN ESKİ ERİŞİLEBİLİR MESAJ**\n\n"
                f"🏷️ **Grup:** `{getattr(chat, 'title', 'Group')}`\n"
                f"👤 **Gönderen:** {user_tag}\n"
                f"🆔 **Mesaj ID:** `{oldest.id}`\n"
                f"📅 **Tarih:** `{oldest.date}`\n"
                f"🔗 **Link:** {link if link else '`link üretilemedi`'}\n\n"
                f"💬 **İçerik:** `{text_preview if text_preview else '—'}`"
            )

            if dm_mode:
                return await client.send_message("me", out)

            await event.edit(out)

        except Exception as e:
            if dm_mode:
                await client.send_message("me", f"❌ Hata: `{str(e)}`")
            else:
                await event.edit(f"❌ Hata: `{str(e)}`")


# ---- HELP ----
from plugins._help import add_help
add_help("tools", ".oldest", "Gruptaki en eski erişilebilir mesajı bulur (binary search).")
add_help("tools", ".oldest dm", "Komutu siler, sonucu sadece sana DM atar.")
