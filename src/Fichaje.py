import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib
import base64

# ==========================================
# CONFIGURATION
# ==========================================

ADMIN_PASSWORD = "admin123"  # 🔐 Change in production
WORKERS_FOLDER = "trabajadores"

# 🔐 Internal system master key (DO NOT MODIFY)
MASTER_KEY = base64.urlsafe_b64encode(
    hashlib.sha256(b"SistemaFichajeUltraSeguro2026").digest()
)
cipher = Fernet(MASTER_KEY)

# Ensure workers folder exists
if not os.path.exists(WORKERS_FOLDER):
    os.makedirs(WORKERS_FOLDER)


# ==========================================
# SECURITY FUNCTIONS
# ==========================================

def hash_password(password: str) -> str:
    """
    Hashes a password using SHA-256.

    Args:
        password (str): Plain text password.

    Returns:
        str: Hashed password in hexadecimal format.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def encrypt_data(data_dict: dict) -> bytes:
    """
    Encrypts a dictionary using Fernet symmetric encryption.

    Args:
        data_dict (dict): Data to encrypt.

    Returns:
        bytes: Encrypted data.
    """
    json_data = json.dumps(data_dict).encode()
    return cipher.encrypt(json_data)


def decrypt_data(encrypted_data: bytes) -> dict:
    """
    Decrypts encrypted data and converts it back to a dictionary.

    Args:
        encrypted_data (bytes): Encrypted input data.

    Returns:
        dict: Decrypted dictionary.
    """
    decrypted = cipher.decrypt(encrypted_data)
    return json.loads(decrypted.decode())


# ==========================================
# MAIN APPLICATION CLASS
# ==========================================

class TimeClockApp:
    """
    Main application class for the secure time tracking system.

    This class manages:
    - User interface (Tkinter)
    - Worker selection
    - Clock-in / clock-out logic
    - Worker management (admin only)
    """

    def __init__(self, root: tk.Tk):
        """
        Initializes the application window and components.

        Args:
            root (tk.Tk): Main Tkinter window.
        """
        self.root = root
        self.root.title("Secure Time Clock System")
        self.root.geometry("900x500")

        self.workers = {}
        self.selected_worker = None

        # Layout configuration
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)

        self.create_widgets()
        self.load_workers()

    # ==========================================
    # UI SETUP
    # ==========================================

    def create_widgets(self):
        """
        Creates and configures all UI components.
        """

        # Left panel (worker list)
        self.left_frame = tk.Frame(self.root)
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.worker_listbox = tk.Listbox(self.left_frame, font=("Arial", 14))
        self.worker_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.worker_listbox.bind("<<ListboxSelect>>", self.select_worker)

        # Right panel (actions)
        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        for i in range(3):
            self.right_frame.rowconfigure(i, weight=1)
        self.right_frame.columnconfigure(0, weight=1)

        # Clock button
        self.clock_button = tk.Button(
            self.right_frame,
            text="CLOCK IN",
            bg="green",
            fg="white",
            font=("Arial", 20),
            command=self.clock_action
        )
        self.clock_button.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)

        # Add worker button
        self.add_button = tk.Button(
            self.right_frame,
            text="Add Worker",
            bg="#ffcc80",
            font=("Arial", 14),
            command=self.add_worker
        )
        self.add_button.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Delete worker button
        self.delete_button = tk.Button(
            self.right_frame,
            text="Delete Worker",
            bg="#ff9999",
            font=("Arial", 14),
            command=self.delete_worker
        )
        self.delete_button.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

    # ==========================================
    # WORKER MANAGEMENT
    # ==========================================

    def load_workers(self):
        """
        Loads all workers from the storage folder and updates the UI list.
        """
        self.worker_listbox.delete(0, tk.END)
        self.workers.clear()

        for file in os.listdir(WORKERS_FOLDER):
            if file.endswith(".dat"):
                name = file.replace(".dat", "")
                self.workers[name] = {"working": False, "start_time": None}
                self.worker_listbox.insert(tk.END, name)

    def select_worker(self, event):
        """
        Handles worker selection from the list.

        Args:
            event: Tkinter event object.
        """
        selection = self.worker_listbox.curselection()
        if selection:
            self.selected_worker = self.worker_listbox.get(selection[0])
            self.update_button()

    def update_button(self):
        """
        Updates the main action button depending on worker state.
        """
        if not self.selected_worker:
            return

        worker = self.workers[self.selected_worker]

        if worker["working"]:
            self.clock_button.config(text="CLOCK OUT", bg="red")
        else:
            self.clock_button.config(text="CLOCK IN", bg="green")

    # ==========================================
    # TIME TRACKING
    # ==========================================

    def clock_action(self):
        """
        Handles clock-in and clock-out actions with password validation.
        """
        if not self.selected_worker:
            messagebox.showwarning("Warning", "Select a worker")
            return

        password = simpledialog.askstring("Password", "Enter password:", show="*")
        if not password:
            return

        file_path = os.path.join(WORKERS_FOLDER, f"{self.selected_worker}.dat")

        with open(file_path, "rb") as f:
            data = decrypt_data(f.read())

        # Password validation
        if data["password_hash"] != hash_password(password):
            messagebox.showerror("Error", "Incorrect password")
            return

        worker = self.workers[self.selected_worker]

        # CLOCK IN
        if not worker["working"]:
            worker["working"] = True
            worker["start_time"] = datetime.now()

            self.worker_listbox.itemconfig(
                self.worker_listbox.curselection(),
                bg="orange"
            )

        # CLOCK OUT
        else:
            end_time = datetime.now()
            start_time = worker["start_time"]

            data["registros"].append({
                "fecha": start_time.strftime("%d/%m/%Y"),
                "inicio": start_time.strftime("%H:%M:%S"),
                "fin": end_time.strftime("%H:%M:%S")
            })

            with open(file_path, "wb") as f:
                f.write(encrypt_data(data))

            worker["working"] = False
            worker["start_time"] = None

            self.worker_listbox.itemconfig(
                self.worker_listbox.curselection(),
                bg="white"
            )

        self.update_button()

    # ==========================================
    # ADMIN FUNCTIONS
    # ==========================================

    def add_worker(self):
        """
        Adds a new worker (admin only).
        """
        admin_pass = simpledialog.askstring("Admin", "Admin password:", show="*")
        if admin_pass != ADMIN_PASSWORD:
            messagebox.showerror("Error", "Incorrect password")
            return

        name = simpledialog.askstring("Name", "Worker name:")
        if not name:
            return

        password = simpledialog.askstring("Password", "Worker password:", show="*")
        if not password:
            return

        file_path = os.path.join(WORKERS_FOLDER, f"{name}.dat")

        if os.path.exists(file_path):
            messagebox.showerror("Error", "Worker already exists")
            return

        data = {
            "password_hash": hash_password(password),
            "registros": []
        }

        with open(file_path, "wb") as f:
            f.write(encrypt_data(data))

        self.load_workers()

    def delete_worker(self):
        """
        Deletes an existing worker (admin only).
        """
        if not self.selected_worker:
            return

        confirm = messagebox.askyesno("Confirm", "Are you sure?")
        if not confirm:
            return

        admin_pass = simpledialog.askstring("Admin", "Admin password:", show="*")
        if admin_pass != ADMIN_PASSWORD:
            messagebox.showerror("Error", "Incorrect password")
            return

        file_path = os.path.join(WORKERS_FOLDER, f"{self.selected_worker}.dat")
        os.remove(file_path)

        self.load_workers()


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    """
    Application entry point.
    Initializes and runs the Tkinter GUI.
    """
    root = tk.Tk()
    app = TimeClockApp(root)
    root.mainloop()