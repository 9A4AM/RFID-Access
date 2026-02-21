import tkinter as tk
from tkinter import ttk, simpledialog
import time
import os

from auth_manager import *
from config_manager import *
from serial_manager import *
from tray_manager import run_tray, show_tray_notification
from startup_manager import add_to_startup
from logger_manager import log_event

init_storage()
init_config()

class RFIDApp:

    def __init__(self, root):
        self.root = root
        self.root.title("RFID Access Control by Mario Ančić")
        self.root.geometry("550x500")
        self.root.configure(bg="#1e1e1e")

        self.buffer = ""
        self.start_time = None

        # Admin / add user state
        self.admin_mode = False
        self.waiting_for_new_user = False

        # Delete confirmation state
        self.delete_waiting_master = False
        self.delete_pending_index = None

        self.create_widgets()
        self.root.bind("<Key>", self.on_key)

        # system tray & autostart
        run_tray(self)
        add_to_startup()

        # Set COM port from config
        config = load_config()
        port_saved = config["SERIAL"].get("port", "")
        if port_saved:
            self.port_combo.set(port_saved)

        # status label init
        if not os.path.exists(MASTER_FILE) or os.path.getsize(MASTER_FILE) == 0:
            self.set_status("Scan MASTER card", color="coral1")
        else:
            self.set_status("Ready: Scan card", color="gold")

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Arial", 12))
        style.configure("TButton", background="#333", foreground="white", font=("Arial", 11))

        # 🔹 Promijenjeno na tk.Label da podrži boje
        self.status_label = tk.Label(self.root, text="", font=("Arial", 14), bg="#1e1e1e", fg="white")
        self.status_label.pack(pady=10)

        self.last_id_label = ttk.Label(self.root, text="Last User: -", font=("Arial", 12))
        self.last_id_label.pack()

        ttk.Label(self.root, text="COM Port:", font=("Arial", 12)).pack(pady=5)
        self.port_combo = ttk.Combobox(self.root, values=list_ports(), font=("Arial", 12))
        self.port_combo.pack()
        ttk.Button(self.root, text="SAVE PORT", command=self.save_port).pack(pady=5)

        ttk.Button(self.root, text="Add User", command=self.enable_add).pack(pady=5)
        ttk.Button(self.root, text="Delete Selected User", command=self.delete_user).pack(pady=5)

        self.user_list = tk.Listbox(self.root, bg="#2b2b2b", fg="white", font=("Arial", 12))
        self.user_list.pack(fill="both", expand=True, pady=10)

        self.refresh_user_list()

    def set_status(self, text, timeout=None, color="white"):
        self.status_label.config(text=text, fg=color)
        if timeout:
            self.root.after(timeout, lambda: self.status_label.config(text="Ready: Scan card", fg="gold"))

    def refresh_user_list(self):
        self.user_list.delete(0, tk.END)
        users = load_users()
        for i, u in enumerate(users):
            try:
                name = fernet.decrypt(u["name"].encode()).decode()
            except:
                name = f"User {i+1}"
            self.user_list.insert(tk.END, name)

    def save_port(self):
        save_serial(self.port_combo.get(), 9600)
        self.set_status(f"COM port saved: {self.port_combo.get()}", timeout=3000, color="gold")

    def enable_add(self):
        self.admin_mode = True
        self.waiting_for_new_user = False
        self.set_status("Scan MASTER to authorize", color="gold")

    def delete_user(self):
        selection = self.user_list.curselection()
        if not selection:
            self.set_status("Select a user to delete", timeout=3000, color="red")
            return
        self.delete_pending_index = selection[0]
        self.delete_waiting_master = True
        self.set_status("Scan MASTER to confirm deletion", color="gold")

    def on_key(self, event):
        if not self.buffer:
             self.start_time = time.time()
        if event.keysym == "Return":
            duration = time.time() - self.start_time
            card_id = self.buffer.strip().upper()
            self.buffer = ""
            if duration > 2:
                return

            # Check if is Master
            if verify_master(card_id):
                user_name = "Master"
                self.last_id_label.config(text=f"Last User: {user_name}", foreground="lightblue")
            else:
                user_name = get_user_name(card_id)
                if not user_name:
                    user_name = "Unknown"
                self.last_id_label.config(text=f"Last User: {user_name}", foreground="white")

            self.process_card(card_id, user_name)
        else:
            self.buffer += event.char

    def process_card(self, card_id, user_name=None):
        if not user_name:
            user_name = get_user_name(card_id) or "Unknown"

        # First time master setup
        if not os.path.exists(MASTER_FILE) or os.path.getsize(MASTER_FILE) == 0:
            save_master(card_id)
            log_event(f"Master created")
            self.set_status("Master saved", timeout=3000, color="gold")
            return

        # DELETE confirmation
        if self.delete_waiting_master:
            if verify_master(card_id):
                delete_user(self.delete_pending_index)
                self.refresh_user_list()
                self.set_status("User deleted", timeout=3000, color="green")
                log_event(f"User {self.delete_pending_index + 1} deleted by MASTER")
            else:
                self.set_status("Deletion denied", timeout=3000, color="red")
                log_event("Deletion denied")
            self.delete_waiting_master = False
            return

        # ADMIN mode
        if self.admin_mode and not self.waiting_for_new_user:
            if verify_master(card_id):
                self.waiting_for_new_user = True
                self.set_status("Scan new user card", color="gold")
                log_event(f"Master authorized admin mode: {user_name}")
            else:
                self.set_status("Admin denied", timeout=3000, color="red")
            return

        # Waiting for new user scan
        if self.waiting_for_new_user:
            name = simpledialog.askstring("New User", "Enter name for new user (optional):")
            add_user(card_id, name)
            final_name = name if name else f"User {len(load_users())}"
            log_event(f"User added: {final_name}")
            self.set_status("User added", timeout=3000, color="light green")
            self.waiting_for_new_user = False
            self.admin_mode = False
            self.refresh_user_list()
            return

        # NORMAL access
        if verify_master(card_id):
            log_event(f"Access granted (MASTER): {user_name}")
            self.set_status(f"Access granted (MASTER): {user_name}", timeout=3000, color="green")
            send_open_command()
            show_tray_notification("RFID Access", f"Master opened door: {user_name}")
            return

        if verify_user(card_id):
            log_event(f"Access granted: {user_name}")
            self.set_status(f"Access granted: {user_name}", timeout=3000, color="green")
            send_open_command()
            show_tray_notification("RFID Access", f"Access granted: {user_name}")
            return

        # Access denied
        log_event(f"Access denied: {user_name if user_name != 'Unknown' else card_id}")
        self.set_status(f"Access denied: {user_name}", timeout=3000, color="red")
        show_tray_notification("RFID Access", f"Access denied: {user_name}")

    def show_window(self):
        self.root.deiconify()
        self.root.after(0, self.root.focus_force())


if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDApp(root)
    root.mainloop()
