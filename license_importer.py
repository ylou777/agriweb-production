# file: license_importer.py
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
from pathlib import Path

# On suppose que vous avez un module license_manager avec LICENSE_FILE
# ou que vous avez défini vous-même la variable LICENSE_FILE ici.
# Par exemple :
from license_manager import LICENSE_FILE

def on_import_license():
    # Ouvre une boîte de dialogue pour sélectionner un fichier licence
    filename = filedialog.askopenfilename(
        title="Sélectionnez votre fichier licence",
        filetypes=[("Licence files", "*.lic"), ("All files", "*.*")]
    )
    if filename:
        # Copie le contenu dans le LICENSE_FILE configuré
        try:
            shutil.copy(filename, LICENSE_FILE)
            messagebox.showinfo("Licence", "Licence importée avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier la licence : {e}")

def main():
    root = tk.Tk()
    root.title("Import de licence")

    # Création d’un bouton pour importer la licence
    btn = tk.Button(root, text="Importer licence", command=on_import_license)
    btn.pack(padx=20, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
