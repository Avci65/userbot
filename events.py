from telethon import events

def register(**kwargs):
    """
    Eski userbot pluginleri gibi decorator döndürür.
    Örn:
    @register(outgoing=True, pattern="^Sa$")
    """
    outgoing = kwargs.pop("outgoing", False)
    incoming = kwargs.pop("incoming", False)

    def decorator(func):
        func.__telethon_handler__ = (events.NewMessage(outgoing=outgoing, incoming=incoming, **kwargs), func)
        return func

    return decorator
