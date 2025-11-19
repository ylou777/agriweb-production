# license_gui.py
import tkinter as tk
from tkinter import filedialog
from license_manager import LICENSE_FILE  # Importez la variable ici

def on_import_license():
    # Ouvre une boîte de dialogue pour sélectionner un fichier licence
    filename = filedialog.askopenfilename(
        title="Sélectionnez votre fichier licence",
        filetypes=[("Licence files", "*.lic"), ("All files", "*.*")]
    )
    if filename:
        # Copie le contenu dans le LICENSE_FILE configuré
        with open(filename, "rb") as src, open(LICENSE_FILE, "wb") as dst:
            dst.write(src.read())
        print("Licence importée avec succès !")

def run_license_gui():
    root = tk.Tk()
    root.title("Importer Licence")
    btn = tk.Button(root, text="Importer licence", command=on_import_license)
    btn.pack(padx=20, pady=20)
    root.mainloop()

if __name__ == "__main__":
    run_license_gui()
