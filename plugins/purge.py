# plugins/purge.py
from telethon import events
from telethon.errors import MessageDeleteForbiddenError, RPCError
import asyncio  # ✅ EKLENDİ

def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(purge)\s*$"))
    async def cmd_purge(event):
        # sadece gruplarda mantıklı
        if event.is_private:
            return await event.edit("❌ `.purge` sadece grup/kanalda çalışır.")

        # reply şart
        if not event.is_reply:
            return await event.edit("❌ Bir mesaja reply yapıp `.purge` yazmalısın.")

        replied = await event.get_reply_message()
        if not replied:
            return await event.edit("❌ Reply mesajı bulunamadı.")

        start_id = replied.id
        end_id = event.id  # purge komut mesajına kadar

        await event.edit("🧹 Temizleniyor...")

        deleted = 0
        batch = []

        try:
            # reply mesajından, .purge mesajına kadar topla
            async for msg in client.iter_messages(event.chat_id, min_id=start_id - 1, max_id=end_id):
                # sadece SENİN mesajların
                if msg.out:
                    batch.append(msg.id)

                # telegram limitleri için parçalı sil
                if len(batch) >= 100:
                    await client.delete_messages(event.chat_id, batch)
                    deleted += len(batch)
                    batch.clear()

            # kalanları sil
            if batch:
                await client.delete_messages(event.chat_id, batch)
                deleted += len(batch)

            # komut mesajını da sil
            try:
                await client.delete_messages(event.chat_id, [event.id])
            except:
                pass

        except MessageDeleteForbiddenError:
            return await event.edit("❌ Silme yetkim yok / bu sohbette mesaj silemiyorum.")
        except RPCError as e:
            return await event.edit(f"❌ Telegram hatası: `{str(e)}`")
        except Exception as e:
            return await event.edit(f"❌ Hata: `{str(e)}`")

        # ✅ bilgi mesajı gönder (bunu 5 sn sonra sil)
        info_msg = await client.send_message(
            event.chat_id,
            f"✅ Purge tamamlandı. Silinen mesaj: **{deleted}**"
        )

        await asyncio.sleep(5)
        try:
            await info_msg.delete()
        except:
            pass


from plugins._help import add_help
add_help("temizlik", ".purge", "Reply’den buraya kadar mesaj siler.")
