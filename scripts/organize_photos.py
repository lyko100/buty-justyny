#!/usr/bin/env python3
"""
Porządkuje folder ze zdjęciami: zamienia bałagan (foldery "New Folder With
Items ...", luźne pliki) na czyste foldery "Para 01", "Para 02", ...
uporządkowane w kolejności robienia zdjęć (po numerze IMG_XXXX).

  - każdy istniejący podfolder ze zdjęciami  -> jedna para
  - luźne pliki                              -> po jednej parze na plik,
    chyba że wpiszesz je razem w GROUP_LOOSE poniżej

Użycie:
    python3 scripts/organize_photos.py "buty Justyny - zdjecia"           # pokazuje plan
    python3 scripts/organize_photos.py "buty Justyny - zdjecia" --apply   # wykonuje

Działa "w miejscu" (przenosi pliki), więc najpierw odpal bez --apply
i sprawdź plan.
"""

import os
import re
import shutil
import sys

IMG_EXT = (".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff")

# Luźne pliki, które NALEŻĄ do tej samej pary (sprawdzone na oko).
# Klucz = dowolna etykieta grupy, wartość = lista nazw plików.
GROUP_LOOSE = {
    "biale-crocsy": ["IMG_6662.HEIC", "IMG_6663.HEIC"],
}


def num(name):
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 10 ** 9


def collect(root):
    pairs = []  # (sort_key, [abs_paths])

    for d in os.listdir(root):
        p = os.path.join(root, d)
        if not os.path.isdir(p) or d.startswith("."):
            continue
        imgs = sorted((f for f in os.listdir(p) if f.lower().endswith(IMG_EXT)), key=num)
        if imgs:
            pairs.append((min(num(f) for f in imgs), [os.path.join(p, f) for f in imgs]))

    loose = sorted((f for f in os.listdir(root)
                    if os.path.isfile(os.path.join(root, f)) and f.lower().endswith(IMG_EXT)),
                   key=num)
    forced = {}
    for label, names in GROUP_LOOSE.items():
        forced.update({n: label for n in names})
    groups = {}
    for f in loose:
        groups.setdefault(forced.get(f, f), []).append(os.path.join(root, f))
    for files in groups.values():
        pairs.append((min(num(os.path.basename(f)) for f in files), sorted(files, key=lambda x: num(os.path.basename(x)))))

    pairs.sort(key=lambda t: t[0])
    return [files for _, files in pairs]


def main(root, apply):
    if not os.path.isdir(root):
        sys.exit(f"Nie znaleziono folderu: {root}")

    pairs = collect(root)
    width = max(2, len(str(len(pairs))))
    print(f"{len(pairs)} par:\n")

    staging = os.path.join(root, ".__organize_tmp")
    if apply:
        if os.path.exists(staging):
            shutil.rmtree(staging)
        os.makedirs(staging)

    for i, files in enumerate(pairs, 1):
        folder = f"Para {i:0{width}d}"
        print(f"{folder}  ({len(files)} zdj.)")
        for j, src in enumerate(files, 1):
            ext = os.path.splitext(src)[1].lower()
            dst_name = f"{j}{ext}"
            print(f"    {os.path.relpath(src, root)}  ->  {folder}/{dst_name}")
            if apply:
                dst_dir = os.path.join(staging, folder)
                os.makedirs(dst_dir, exist_ok=True)
                shutil.move(src, os.path.join(dst_dir, dst_name))

    if not apply:
        print("\n(to był tylko plan — dodaj --apply, żeby wykonać)")
        return

    # remove old empty dirs, then swap staged folders in
    for d in list(os.listdir(root)):
        p = os.path.join(root, d)
        if os.path.isdir(p) and d != ".__organize_tmp":
            shutil.rmtree(p)
    for d in os.listdir(staging):
        shutil.move(os.path.join(staging, d), os.path.join(root, d))
    shutil.rmtree(staging)
    print(f"\nGotowe. Teraz:  python3 scripts/import_shoes.py \"{root}\"")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)
    main(os.path.expanduser(args[0].rstrip("/")), apply="--apply" in sys.argv)
