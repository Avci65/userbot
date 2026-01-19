# plugins/help.py
from telethon import events
from plugins._help import render_help

def setup(client):

    @client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.(help|cmds)(?:\s+(\w+))?\s*$"))
    async def cmd_help(event):
        cat = event.pattern_match.group(2)
        await event.edit(render_help(cat))
