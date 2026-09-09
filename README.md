# 👟 Buty: zostają czy na wyrzut?

Mała aplikacja w stylu Tindera do przeglądania butów. Justyna ogląda po kolei
zdjęcia każdej pary i klika **✓ ZOSTAJE** albo **✗ NA WYRZUT**. Wszystkie
odpowiedzi lądują w bazie, a Marta ogląda je na żywo na stronie **/wyniki**.

- `/` – ekran startowy (podajesz imię)
- `/oceniaj?kto=Imię` – przeglądanie butów, dwa duże przyciski
- `/wyniki` – podsumowanie: co zostaje, co na wyrzut, filtr, podgląd zdjęć, CSV

Stos: Flask (Python) + zwykły HTML/JS + Postgres, hosting na Vercel
(`@vercel/python`). Zoptymalizowane pod telefon.

---

## Kto co robi

| | Link | Na czym |
|---|---|---|
| **Justyna** | `https://<adres>/oceniaj?kto=Justyna` | telefon – tylko klika ✓ / ✗, nic nie pobiera |
| **Marta (podgląd)** | `https://<adres>/wyniki` | telefon/komputer – widzi odpowiedzi Justyny na żywo |
| **Marta (testy)** | `https://<adres>/oceniaj?kto=test-marta` | odpowiedzi z „test" w imieniu są w wynikach domyślnie ukryte |

Justyna **nie musi niczego pobierać ani wysyłać** – każde kliknięcie od razu
zapisuje się we wspólnej bazie. Marta w dowolnej chwili otwiera `/wyniki`
(warto dodać do zakładek / ekranu głównego telefonu) i widzi wszystko.
Przycisk „Pobierz CSV" na stronie wyników to tylko dodatek dla Marty, gdyby
chciała mieć to w arkuszu.

---

## Zdjęcia

64 foldery + luźne pliki z `buty Justyny - zdjecia/` zostały uporządkowane w
**68 par** (`Para 1` … `Para 68`, w kolejności robienia zdjęć) i skompresowane
do `static/shoes/` (28 MB, 187 zdjęć). Surowy folder jest w `.gitignore`.

Gdyby trzeba było powtórzyć (np. po dorzuceniu zdjęć):

```bash
python3 scripts/organize_photos.py "buty Justyny - zdjecia"          # pokazuje plan
python3 scripts/organize_photos.py "buty Justyny - zdjecia" --apply  # porządkuje w foldery Para NN
python3 scripts/import_shoes.py    "buty Justyny - zdjecia"          # kompresuje + robi manifest.json
```

Skrypty używają wbudowanego w macOS `sips` (obsługuje HEIC) – nic nie instalujesz.

---

## Uruchomienie lokalnie

```bash
cd ~/Documents/buty-tinder && ./run.sh
```

`http://localhost:8080`. Bez `DATABASE_URL` używa lokalnego pliku
`shoes.db` (SQLite), więc testujesz bez żadnej bazy.

---

## Wrzucenie na GitHub

Repo: **`lyko100/buty-justyny`** (już utworzone). Z katalogu projektu:

```bash
git remote add origin https://github.com/lyko100/buty-justyny.git
git push -u origin main
```

(remote jest już ustawiony – wystarczy `git push -u origin main`)

## Vercel

Projekt jest połączony z repo, więc po `git push` sam się zbuduje. Potrzebna
jest jeszcze **baza danych**:

1. Vercel → projekt `buty-justyny` → zakładka **Storage** → **Create Database**
   → **Postgres** → *Create*. Vercel sam podłączy zmienne (`POSTGRES_URL` itd.)
   do projektu – aplikacja je rozpozna, nie trzeba nic wpisywać ręcznie.
2. Zakładka **Deployments** → przy ostatnim wpisie **Redeploy** (żeby złapał
   nową zmienną).

To jest osobna baza, nic wspólnego z „when are you free".

Gdybyś wolała wpisać ręcznie: w **Settings → Environment Variables** dodaj
`DATABASE_URL` = connection string z dowolnego Postgresa (np. darmowy
[Neon](https://neon.tech)).

---

## Jak działa „kto co zaznaczył"

Każde kliknięcie zapisuje wiersz: `para` · `kto` (imię z linku) · `decyzja` ·
`kiedy`. Na `/wyniki` wybierasz z listy, czyje odpowiedzi oglądać. Jedna para =
jedna decyzja na osobę (ostatnią można cofnąć w trakcie). Wejście drugi raz tym
samym linkiem wznawia od pierwszej nieocenionej pary.
