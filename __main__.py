from start_gpio_daemon import start_gpio_loop
from start_pibooth_gui import start_gui
from threading import Thread

# erstelle gpio thread und starte diesen
Thread(target=start_gpio_loop, name="gpio_daemon", daemon=True).start()

# starte pibooth gui
start_gui()
