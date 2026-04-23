import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from cryptography.fernet import Fernet
import hashlib
import base64
import json

# ==========================================
# CONFIGURATION
# ==========================================

ADMIN_PASSWORD = "admin123"  # 🔐 Change in production

# 🔐 Same master key used in the main system (must match)
MASTER_KEY = base64.urlsafe_b64encode(
    hashlib.sha256(b"SistemaFichajeUltraSeguro2026").digest()
)
cipher = Fernet(MASTER_KEY)


# ==========================================
# DECRYPTION FUNCTION
# ==========================================

def decrypt_file():
    """
    Handles the secure decryption of a worker's time record file.

    Workflow:
    1. Requests admin authentication
    2. Allows file selection (.dat)
    3. Decrypts file content
    4. Displays formatted work records in a new window

    Raises:
        Shows error message if:
        - Admin password is incorrect
        - File is invalid or corrupted
    """

    # Admin authentication
    admin_pass = simpledialog.askstring("Admin", "Admin password:", show="*")
    if admin_pass != ADMIN_PASSWORD:
        messagebox.showerror("Error", "Incorrect password")
        return

    # File selection
    file_path = filedialog.askopenfilename(
        filetypes=[("DAT Files", "*.dat")]
    )
    if not file_path:
        return

    try:
        # Read and decrypt file
        with open(file_path, "rb") as f:
            data = json.loads(cipher.decrypt(f.read()).decode())

        # Format output
        text_output = ""

        for record in data["registros"]:
            text_output += (
                f"Date: {record['fecha']}\n"
                f"Start: {record['inicio']}\n"
                f"End: {record['fin']}\n"
                f"----------------------\n"
            )

        # Create result window
        result = tk.Toplevel(root)
        result.title("Decrypted Records")

        text = tk.Text(result, width=80, height=30)
        text.pack()

        text.insert(tk.END, text_output)

    except Exception:
        # Error handling (invalid file, wrong format, etc.)
        messagebox.showerror("Error", "Invalid or corrupted file")


# ==========================================
# MAIN WINDOW
# ==========================================

root = tk.Tk()
root.title("Secure Decryption Tool")
root.geometry("400x200")

btn = tk.Button(
    root,
    text="Decrypt File",
    font=("Arial", 14),
    command=decrypt_file
)
btn.pack(expand=True)

# ==========================================
# ENTRY POINT
# ==========================================

root.mainloop()