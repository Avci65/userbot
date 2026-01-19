# plugins/_help.py
from typing import Dict, List, Tuple

# kategori -> [(komut, açıklama), ...]
HELP_REGISTRY: Dict[str, List[Tuple[str, str]]] = {}

def add_help(category: str, command: str, description: str):
    """
    Plugin içinden çağrılır.
    add_help("pmguard", ".pmguard on/off", "PM Guard aç/kapat")
    """
    category = category.strip().lower()
    HELP_REGISTRY.setdefault(category, [])
    HELP_REGISTRY[category].append((command.strip(), description.strip()))

def render_help(category: str | None = None) -> str:
    if not HELP_REGISTRY:
        return "❌ Help kayıtları yok."

    if category:
        cat = category.strip().lower()
        items = HELP_REGISTRY.get(cat)
        if not items:
            cats = ", ".join(sorted(HELP_REGISTRY.keys()))
            return f"❌ `{cat}` diye bir kategori yok.\n\nMevcut: `{cats}`"

        text = [f"📌 **{cat.upper()} KOMUTLARI**\n"]
        for cmd, desc in items:
            text.append(f"• `{cmd}` → {desc}")
        return "\n".join(text)

    # genel help
    text = ["📌 **USERBOT KOMUTLARI**\n"]
    for cat in sorted(HELP_REGISTRY.keys()):
        text.append(f"\n🧩 **{cat.upper()}**")
        for cmd, desc in HELP_REGISTRY[cat]:
            text.append(f"• `{cmd}` → {desc}")

    text.append("\n\n🔎 Detay: `.help <kategori>`  (örn: `.help pmguard`)")
    return "\n".join(text)
