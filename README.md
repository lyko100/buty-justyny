# 👟 Buty: zostają czy na wyrzut?

Mała aplikacja w stylu Tindera do przeglądania butów. Justyna ogląda po kolei
zdjęcia każdej pary i klika **✓ ZOSTAJE** albo **✗ NA WYRZUT**. Wszystkie
odpowiedzi lądują w bazie, a Wy oglądacie je na stronie **/wyniki**.

- `/` – ekran startowy (podajesz imię)
- `/oceniaj` – przeglądanie butów, dwa duże przyciski
- `/wyniki` – podsumowanie: co zostaje, co na wyrzut, filtr, eksport do CSV

## Stos

Flask (Python) + zwykły HTML/JS + Postgres, hostowane na Vercel — tak samo jak
projekt „when are you free". Zdjęcia leżą w repo w `static/shoes/`.

---

## 1. Uruchomienie lokalnie (do testów)

```bash
cd ~/Documents/buty-tinder
./run.sh
```

Otworzy się na `http://localhost:8080`. Bez ustawionej zmiennej `DATABASE_URL`
używa lokalnego pliku `shoes.db` (SQLite) — nic nie trzeba instalować.

## 2. Wgranie zdjęć butów

Surowe zdjęcia leżą w `buty Justyny - zdjecia/` (ten folder jest w `.gitignore`,
nie trafia do repo — 188 plików HEIC, ok. 500 MB).

**Ułóż zdjęcia w podfolderach — jeden podfolder = jedna para butów.**
Nazwy podfolderów: `01`, `02`, `03` … (albo `czarne kozaki`, jeśli chcesz
własny podpis). Kolejność jest sortowana naturalnie, więc `10` wypada po `9`.

```
buty Justyny - zdjecia/
  01/   IMG_6617.HEIC  IMG_6618.HEIC  IMG_6619.HEIC
  02/   IMG_6620.HEIC  IMG_6621.HEIC
  03/   ...
```

Potem:

```bash
python3 scripts/import_shoes.py "buty Justyny - zdjecia"
```

Skrypt (używa wbudowanego w macOS `sips`, obsługuje HEIC — nic nie trzeba
instalować) zmniejszy i skompresuje zdjęcia, zapisze je w `static/shoes/`
i nadpisze `static/shoes/manifest.json` (usuwając przykładowe buty).
Oryginały zostają nietknięte. W wynikach pary będą podpisane „Para 1", „Para 2", …

```bash
git add -A && git commit -m "Dodaj zdjęcia butów" && git push
```

## 3. Wrzucenie do GitHuba (pierwszy raz)

Załóż puste repo na <https://github.com/new> (np. `buty-tinder`), bez README, a potem:

```bash
cd ~/Documents/buty-tinder
git add -A
git commit -m "Pierwsza wersja"
git branch -M main
git remote add origin https://github.com/lyko100/buty-tinder.git
git push -u origin main
```

## 4. Hosting na Vercel

1. <https://vercel.com/new> → zaimportuj repo `buty-tinder`.
2. W ustawieniach projektu → **Environment Variables** dodaj `DATABASE_URL`.
   Możesz użyć **tej samej** bazy co „when are you free" (aplikacja tworzy
   własną tabelę `shoe_votes`, nie koliduje) albo założyć nową bazę Postgres
   (Vercel → Storage → Postgres, albo darmowy [Neon](https://neon.tech)).
3. **Deploy**.

Adres wyjdzie np. `https://buty-tinder.vercel.app`.

## 5. Rozesłanie linków

- **Dla Justyny:** `https://buty-tinder.vercel.app/oceniaj?kto=Justyna`
- **Do testów (żeby nie mieszać z jej odpowiedziami):**
  `https://buty-tinder.vercel.app/oceniaj?kto=test-marta`
  — każde imię ze słowem „test" jest na `/wyniki` domyślnie ukryte
  (jest przełącznik „pokaż odpowiedzi testowe").
- **Dla Was, do sprawdzania:** `https://buty-tinder.vercel.app/wyniki`

## Jak to działa z „kto co zaznaczył"

Każde kliknięcie zapisuje w bazie wiersz: `która para`, `kto` (imię z linku),
`decyzja`, `kiedy`. Na `/wyniki` wybierasz z listy czyje odpowiedzi chcesz
zobaczyć. „Pobierz CSV" ściąga wszystko do arkusza.

Jedna para = jedna decyzja na osobę (można cofnąć ostatnią w trakcie
oceniania). Jak ktoś wejdzie drugi raz tym samym linkiem, aplikacja wznawia
od pierwszej nieocenionej pary.
