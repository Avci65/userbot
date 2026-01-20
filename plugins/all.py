# plugins/all.py
import random
import asyncio
from telethon import events

# aktif all işlemleri: chat_id -> True/False
ALL_RUNNING = {}

def setup(client):

    # .all 25 sebep
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(all)(?:\s+(\d+))?(?:\s+([\s\S]+))?$"))
    async def cmd_all(event):
        if event.is_private:
            return

        chat_id = event.chat_id

        # zaten çalışıyorsa engelle
        if ALL_RUNNING.get(chat_id):
            return await event.edit("⚠️ Bu grupta zaten `.all` çalışıyor. Durdurmak için: `.stopall`")

        n_str = event.pattern_match.group(2)
        extra_text = (event.pattern_match.group(3) or "").strip()

        n = 25
        if n_str:
            try:
                n = int(n_str)
            except:
                n = 25

        n = max(1, min(n, 50))

        await event.delete()

        # gruptaki kullanıcıları çek
        users = []
        async for u in client.iter_participants(chat_id):
            if u.bot:
                continue
            users.append(u)

        if not users:
            return

        # random seç
        chosen = random.sample(users, k=min(n, len(users)))

        # döngü başlat
        ALL_RUNNING[chat_id] = True

        try:
            # İstersen tek mesaj yerine sırayla spam yapalım:
            # Her user için 1 mesaj (durdurulabilir)
            for u in chosen:
                if not ALL_RUNNING.get(chat_id):
                    break

                name = (u.first_name or "User").replace("[", "").replace("]", "")
                msg = f"[{name}](tg://user?id={u.id})"
                if extra_text:
                    msg += f" {extra_text}"

                await client.send_message(chat_id, msg, link_preview=False)

                # flood yememek için küçük bekleme
                await asyncio.sleep(1.2)

        finally:
            ALL_RUNNING[chat_id] = False


    # ✅ durdurma komutu
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(stopall)\s*$"))
    async def cmd_stopall(event):
        if event.is_private:
            return
        chat_id = event.chat_id

        if not ALL_RUNNING.get(chat_id):
            return await event.edit("ℹ️ Bu grupta çalışan bir `.all` yok.")

        ALL_RUNNING[chat_id] = False
        await event.edit("✅ `.all` durduruldu.")
from plugins._help import add_help
add_help("herkesi etiketleme", ".all veye .all 25 (sebeb)", "etiket atmak için vardır")
