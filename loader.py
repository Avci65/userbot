import os
import importlib.util

def load_plugins(client, plugins_dir="plugins"):
    if not os.path.isdir(plugins_dir):
        return

    for file in os.listdir(plugins_dir):
        if not file.endswith(".py"):
            continue

        path = os.path.join(plugins_dir, file)
        name = f"plugins.{file[:-3]}"

        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # plugin içindeki register edilmiş handlerları client'a bağla
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if hasattr(attr, "__telethon_handler__"):
                ev, fn = attr.__telethon_handler__
                client.add_event_handler(fn, ev)
