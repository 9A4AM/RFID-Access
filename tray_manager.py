from pystray import Icon, MenuItem, Menu
from PIL import Image
import threading
import os

# globalna referenca na tray icon za notifikacije
tray_icon = None

def run_tray(app):
    global tray_icon
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        icon_image = Image.open(icon_path)
    else:
        # zelena kockica 16x16 px
        icon_image = Image.new('RGB', (16, 16), color=(0, 255, 0))

    menu = Menu(
        MenuItem("Show Window", lambda icon, item: show_window_safe(app)),
        MenuItem("Exit", lambda icon, item: exit_app(icon, app))
    )

    tray_icon = Icon("RFID Access", icon_image, "RFID Control", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

    # Override close button da samo sakrije GUI
    def on_close():
        app.root.withdraw()
    app.root.protocol("WM_DELETE_WINDOW", on_close)


def show_window_safe(app):
    # Tkinter GUI mora se pozvati iz glavne niti
    app.root.after(0, lambda: app.root.deiconify())
    app.root.after(0, lambda: app.root.focus_force())


def exit_app(icon, app):
    icon.stop()
    app.root.after(0, app.root.destroy)


def show_tray_notification(title, msg):
    """Prikaz tray balon notifikacije"""
    global tray_icon
    if tray_icon:
        tray_icon.notify(msg, title)
