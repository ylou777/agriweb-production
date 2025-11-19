#!/usr/bin/env python
"""
Petit utilitaire pour fusionner des PDF.
- Fonctionne avec pypdf (pip install pypdf)
- Par défaut, fusionne les 2 fichiers fournis par l'utilisateur et écrit un PDF fusionné sur le Bureau.

Utilisation:
  python tools/merge_pdfs.py
  # ou avec des chemins personnalisés (ordre conservé)
  python tools/merge_pdfs.py "C:\\chemin\\vers\\a.pdf" "C:\\chemin\\vers\\b.pdf" -o "C:\\chemin\\sortie.pdf"
"""
from __future__ import annotations
import argparse
import os
import sys

try:
    from pypdf import PdfReader, PdfWriter
except Exception as e:
    print("Le module 'pypdf' est requis. Installez-le par: pip install pypdf", file=sys.stderr)
    raise


def merge_pdfs(input_files: list[str], output_path: str) -> None:
    if not input_files:
        raise ValueError("Aucun fichier d'entrée fourni")

    for p in input_files:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Fichier introuvable: {p}")

    out_dir = os.path.dirname(output_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    writer = PdfWriter()

    for pdf_path in input_files:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"✅ Fusion terminée: {output_path}")


def main() -> int:
    default_inputs = [
        r"C:\\Users\\Utilisateur\\Desktop\\Rapport Géospatial Exhaustif - AgriWeb_gueret 1108.pdf",
        r"C:\\Users\\Utilisateur\\Desktop\\Rapport Complet - Guéret_11_08_2025.pdf",
    ]
    default_output = r"C:\\Users\\Utilisateur\\Desktop\\Rapport_Fusionne.pdf"

    parser = argparse.ArgumentParser(description="Fusionne des fichiers PDF dans l'ordre fourni")
    parser.add_argument("inputs", nargs="*", help="Fichiers PDF d'entrée (ordre conservé)")
    parser.add_argument("-o", "--output", default=default_output, help="Chemin de sortie du PDF fusionné")
    args = parser.parse_args()

    inputs = args.inputs or default_inputs
    try:
        merge_pdfs(inputs, args.output)
        return 0
    except Exception as e:
        print(f"❌ Erreur de fusion: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
