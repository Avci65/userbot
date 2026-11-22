# plugins/filter.py
import os
import json
import redis
from telethon import events

def setup(client):
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    REDIS_URL = os.getenv("REDIS_URL", "").strip()

    if not REDIS_URL:
        print("⚠️ filter.py: REDIS_URL yok, filter sistemi çalışmayacak.")
        return

    rdb = redis.from_url(REDIS_URL, decode_responses=True)

    def is_owner(event) -> bool:
          return event.out

    def _key(chat_id: int) -> str:
        # ✅ Her grup için ayrı key (bu yüzden A/B farklı çalışır)
        return f"filters:{chat_id}"

    def load_filters(chat_id: int):
        raw = rdb.get(_key(chat_id))
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except:
            return {}

    def save_filters(chat_id: int, filters: dict):
        rdb.set(_key(chat_id), json.dumps(filters, ensure_ascii=False))

    # ✅ .filter sa as  -> sadece o gruba ekler
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(filter)\s+(\S+)\s+(.+)$"))
    async def cmd_filter(event):
        if not is_owner(event):
            return

        if not event.is_group:
            return await event.edit("❌ `.filter` sadece gruplarda çalışır.")

        chat_id = event.chat_id
        word = event.pattern_match.group(2).strip().lower()
        reply_text = event.pattern_match.group(3).strip()

        filters = load_filters(chat_id)
        filters[word] = reply_text
        save_filters(chat_id, filters)

        await event.edit(f"✅ Filter eklendi (**sadece bu grup**):\n`{word}` → `{reply_text}`")

    # ✅ .filters  -> sadece o grubun filtreleri
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(filters)\s*$"))
    async def cmd_filters(event):
        if not is_owner(event):
            return

        if not event.is_group:
            return await event.edit("❌ `.filters` sadece gruplarda çalışır.")

        chat_id = event.chat_id
        filters = load_filters(chat_id)

        if not filters:
            return await event.edit("📭 Bu grupta hiç filter yok.")

        msg = f"📌 **Bu grubun filtreleri ({len(filters)}):**\n\n"
        for k, v in filters.items():
            msg += f"• `{k}` → `{v}`\n"

        await event.edit(msg)

    # ✅ .filterdel sa  -> sadece o gruptan siler
    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(filterdel)\s+(\S+)\s*$"))
    async def cmd_filterdel(event):
        if not is_owner(event):
            return

        if not event.is_group:
            return await event.edit("❌ `.filterdel` sadece gruplarda çalışır.")

        chat_id = event.chat_id
        word = event.pattern_match.group(2).strip().lower()

        filters = load_filters(chat_id)
        if word not in filters:
            return await event.edit(f"❌ `{word}` filtresi bu grupta yok.")

        del filters[word]
        save_filters(chat_id, filters)

        await event.edit(f"🗑️ `{word}` filtresi **bu gruptan** silindi ✅")

    # ✅ incoming: sadece o grup için filtre uygula
    @client.on(events.NewMessage(incoming=True))
    async def auto_filter(event):
        try:
            if not event.is_group:
                return

            # Owner kendi mesajına cevap vermesin
            if OWNER_ID != 0 and event.sender_id == OWNER_ID:
                return

            chat_id = event.chat_id
            text = (event.raw_text or "").strip().lower()
            if not text:
                return

            filters = load_filters(chat_id)
            if not filters:
                return

            # ✅ tam eşleşme: "sa" yazılırsa sadece "sa" filtresi tetiklenir
            if text in filters:
                await event.reply(filters[text])

        except Exception as e:
            print("filter error:", e)

    print("✅ filter.py (gruba özel) plugin yüklendi")


# ---- HELP ----
from plugins._help import add_help
add_help("filter", ".filter <kelime> <cevap>", "Bu gruba özel filter ekler. Örn: `.filter sa as`")
add_help("filter", ".filters", "Bu gruptaki filterleri listeler.")
add_help("filter", ".filterdel <kelime>", "Bu gruptan filter siler. Örn: `.filterdel sa`")
