#!/usr/bin/env python3
"""
Wgraj zdjęcia butów do aplikacji.

Ułóż zdjęcia w podfolderach — jeden podfolder = jedna para butów:

    buty/
      01/  IMG_6617.HEIC  IMG_6618.HEIC  IMG_6619.HEIC
      02/  IMG_6620.HEIC  IMG_6621.HEIC
      03/  ...

Nazwy podfolderów służą tylko do kolejności (sortowane naturalnie: 1, 2, ... 10).
W wynikach pary są podpisane „Para 1", „Para 2", ... — chyba że nazwa folderu
zawiera litery (np. „czarne kozaki"), wtedy używana jest ta nazwa.

Użycie:
    python3 scripts/import_shoes.py "buty Justyny - zdjecia"

Skrypt zmniejsza i kompresuje zdjęcia (macOS `sips`, obsługuje HEIC),
zapisuje je w static/shoes/ i tworzy static/shoes/manifest.json.
Oryginały zostają nietknięte. Potem:
    git add -A && git commit -m "Dodaj zdjęcia butów" && git push
"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOES_DIR = os.path.join(ROOT, "static", "shoes")
MANIFEST = os.path.join(SHOES_DIR, "manifest.json")

MAX_EDGE = 1200          # dłuższy bok zdjęcia po zmniejszeniu
QUALITY = 55             # jakość JPEG (0-100); 55 = małe pliki, w zupełności czytelne
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def label_for(folder_name, index):
    # jeśli w nazwie folderu są litery (poza słowem "para") — użyj jej jako podpisu
    cleaned = re.sub(r"(?i)\bpara\b", "", folder_name).strip(" -_")
    if re.search(r"[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", cleaned):
        return cleaned
    return f"Para {index}"


def convert(src_path, dst_path):
    subprocess.run(
        ["sips", "-Z", str(MAX_EDGE), "-s", "format", "jpeg",
         "-s", "formatOptions", str(QUALITY), src_path, "--out", dst_path],
        check=True, capture_output=True,
    )


def main(src):
    if shutil.which("sips") is None:
        sys.exit("Potrzebny jest program `sips` (jest wbudowany w macOS).")
    if not os.path.isdir(src):
        sys.exit(f"Nie znaleziono folderu: {src}")

    subdirs = sorted(
        (d for d in os.listdir(src)
         if os.path.isdir(os.path.join(src, d)) and not d.startswith(".")),
        key=natural_key,
    )
    if not subdirs:
        sys.exit(
            "Nie znalazłem podfolderów. Ułóż zdjęcia tak, żeby każda para\n"
            "była w osobnym podfolderze (01/, 02/, 03/ ...), potem uruchom skrypt ponownie."
        )

    # skasuj wcześniej wygenerowane pary i przykłady
    if os.path.isdir(SHOES_DIR):
        for name in os.listdir(SHOES_DIR):
            full = os.path.join(SHOES_DIR, name)
            if os.path.isdir(full) and (name.startswith("para-") or name.startswith("demo-")):
                shutil.rmtree(full)
    os.makedirs(SHOES_DIR, exist_ok=True)

    manifest = {"shoes": []}
    skipped = 0
    for i, folder in enumerate(subdirs, 1):
        src_dir = os.path.join(src, folder)
        imgs = sorted(
            (f for f in os.listdir(src_dir)
             if os.path.splitext(f)[1].lower() in EXTS and not f.startswith(".")),
            key=natural_key,
        )
        if not imgs:
            print(f"  (pomijam pusty folder: {folder})")
            continue

        slug = f"para-{i:02d}"
        out_dir = os.path.join(SHOES_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        photos = []
        for j, name in enumerate(imgs, 1):
            out_name = f"{j}.jpg"
            try:
                convert(os.path.join(src_dir, name), os.path.join(out_dir, out_name))
                photos.append(f"/static/shoes/{slug}/{out_name}")
            except subprocess.CalledProcessError:
                skipped += 1
                print(f"  ! nie udało się przetworzyć {folder}/{name}")

        if photos:
            label = label_for(folder, i)
            manifest["shoes"].append({"id": slug, "label": label, "photos": photos})
            print("  {}  {}  - {} zdj.".format(slug, label, len(photos)))
        else:
            shutil.rmtree(out_dir)

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    total_photos = sum(len(s["photos"]) for s in manifest["shoes"])
    print(f"\nGotowe: {len(manifest['shoes'])} par, {total_photos} zdjęć.")
    if skipped:
        print(f"Pominięto {skipped} plików.")
    print("Teraz:  git add -A && git commit -m \"Dodaj zdjęcia butów\" && git push")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(os.path.expanduser(sys.argv[1].rstrip("/")))
