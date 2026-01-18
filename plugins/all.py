# plugins/all.py
import random
from telethon import events

def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(all)(?:\s+(\d+))?(?:\s+(.+))?$"))
    async def cmd_all(event):
        """
        .all 25 sebep
        .all 25
        .all sebep (sayı yoksa default 25)
        """
        if event.is_private:
            return

        n_str = event.pattern_match.group(2)
        extra_text = (event.pattern_match.group(3) or "").strip()

        # eğer kullanıcı ".all sebep" yazdıysa, 2. grup None olur ama 3. grup da None olur.
        # bu yüzden ek kontrol:
        raw = event.raw_text.strip()
        parts = raw.split(maxsplit=1)

        # varsayılan
        n = 25

        # ".all 25 ..." formatı
        if n_str:
            try:
                n = int(n_str)
            except:
                n = 25
        else:
            # ".all sebep" yazıldıysa sayıyı default 25 yapıyoruz ve sebebi alıyoruz
            if len(parts) == 2 and not parts[1].strip().isdigit():
                extra_text = parts[1].strip()

        # Limitler (spam yememek için güvenli)
        n = max(1, min(n, 50))

        await event.delete()

        # gruptaki kişilerden çek
        users = []
        async for u in client.iter_participants(event.chat_id):
            # botları ve kendimizi geç
            if u.bot:
                continue
            users.append(u)

        if not users:
            return

        # random seç
        chosen = random.sample(users, k=min(n, len(users)))

        # tek mesajda etiketlemek daha iyi (ban yemeyi azaltır)
        tags = []
        for u in chosen:
            name = (u.first_name or "User").replace("[", "").replace("]", "")
            tags.append(f"[{name}](tg://user?id={u.id})")

        text = " ".join(tags)
        if extra_text:
            text += f"\n\n{extra_text}"

        await client.send_message(event.chat_id, text, link_preview=False)
