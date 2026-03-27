# Aplicatie sesizari

> Aplicatie web de raportare a incidentelor/neregulilor din localitate, identificate de localnici, cu redirectare catre un departament sau institutie avizata.


## Ce poate face

- autentificare cu 3 roluri: `citizen`, `operator`, `dispecer`, `admin`
- creare sesizare cu titlu, descriere, adresa, categorie, prioritate si coordonate pe harta
- listare sesizari cu filtre si afisare pe harta
- pagina de detaliu cu istoric de actualizari, vot, follow si raportare
- dashboard dispecer pentru trierea sesizarilor si redirectare catre operatori
- dashboard operator pentru schimbare status si redirectare inapoi la triaj
- notificari interne, prin email si Web Push pentru urmaritorii unei sesizari
- dashboard admin pentru departamente, categorii si operatori

## Stack ales

- `Python`
  - limbajul principal; l-am ales pentru ca ne este mai familiar
- `Flask`
  - tine rutele web si API-ul mic pentru marker-ele de pe harta si contorul de notificari
- `Flask-SQLAlchemy`
  - tine modelele si relatiile dintre tabele
- `Flask-Login`
  - rezolva login, logout si sesiunea utilizatorului
- `SQLite`
  - baza de date locala, foarte simpla pentru inceput si foarte potrivita pentru dispozitivul Raspberry Pi pe care am instalat serverul. Parolele sunt criptate si stocate in forma de hash.
- `Jinja2`
  - genereaza HTML pe server
- `Vanilla JavaScript`
  - pentru harta, compresie si validare imagini uploadate, formulare accesibile si activare Web Push
- `Leaflet + OpenStreetMap`
  - pentru pozitionare pe harta si afisarea marker-elor
- `pywebpush`
  - pentru livrarea notificarilor Web Push catre dispozitivele abonate

### Dependinte de sistem

Pe masina de dezvoltare sau pe Raspberry Pi aveti nevoie de:

- `python3`
- `python3-venv`
- `python3-pip`

Pe Debian, Ubuntu sau Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### Dependinte Python

Acestea sunt deja declarate in `requirements.txt`:

- `Flask`
- `Flask-Login`
- `Flask-SQLAlchemy`
- `waitress`
- `pywebpush`

## De ce am ales acest stack

### Criterii

- sa fie usor de invatat si depanat
- sa poata fi terminat intr-un timp scurt
- sa ruleze bine pe Raspberry Pi 5
- sa permita o interfata clara si accesibila
- sa nu introduca prea multe unelte simultan

### Argumente

- `Flask` este mai usor pentru incepatori decat un stack cu frontend separat si API mare.
- `SQLite` elimina un server separat de baza de date in prima etapa.
- `Jinja` permite sa vedeti direct legatura intre datele din Python si HTML-ul din browser.
- `Leaflet` adauga harta fara build complex.
- `Vanilla JS` pentru procesare pe frontend.

## Cum interactioneaza tehnologiile

1. Browser-ul cere o pagina Flask.
2. Ruta Flask apeleaza un service.
3. Service-ul valideaza datele si apeleaza repository-urile.
4. Repository-urile citesc sau scriu in SQLite prin SQLAlchemy.
5. Flask trimite HTML-ul randat cu Jinja.
6. Pentru harta, contorul de notificari si abonarea Web Push, pagina mai face si cateva cereri JSON mici.

## Conturi demo dupa `python seed.py`

- admin: `admin@t.t` / `admin123`
- dispatcher: `dispatcher@t.t` / `dispatcher123`
- operator: `operator@t.t` / `operator123`
- cetatean: `cetatean@t.t` / `cetatean123`

## Pornire rapida

```bash
cd "Aplicatie sesizari"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python run.py
```

Aplicatia se deschide apoi la:

```text
http://127.0.0.1:5000
```

Ideea este simpla:

- codul proiectului se muta
- lista de dependinte se muta
- mediul virtual se reconstruieste local pe masina tinta

## Fisiere importante

- `BEGINNER_GUIDE.md`
  - ghid simplu, pas cu pas
- `ARCHITECTURE.md`
  - explica cine vorbeste cu cine
- `DATABASE.md`
  - explica tabelele si relatiile
- `DEPLOYMENT.md`
  - pasi pentru Raspberry Pi si rulare in retea
- `app/`
  - tot codul aplicatiei

## Observatii pentru concurs

- proiectul este gandit ca `MVP sigur`, nu ca demo cu multe tehnologii spectaculoase
- accentul este pe functionalitate, organizarea datelor si claritatea fluxului
- baza este pregatita pentru extinderi viitoare: coada separata pentru email/push, moderare mai avansata si agregare duplicate

## Accesibilitate

Am tratat accesibilitatea ca parte din proiect, nu ca polish final:

- interfata urmeaza tema sistemului si are panou vizibil pentru marime text, contrast si reducerea miscarii
- focusul este vizibil pe controalele interactive
- formularele importante au label-uri explicite, `autocomplete` unde are sens si sumar de erori
- sesizarea poate fi trimisa fara mouse, prin coordonate introduse manual
- mesajele flash, statusurile de upload si contorul de notificari au etichete mai bune pentru screen reader
- pagina de detaliu are actiuni inline mai clare pentru Narrator/NVDA: vot, follow, raportare si moderare
- exista un `live region` global folosit pentru feedback generat in browser

Pentru demonstratie:

- puteti arata `skip-link`
- puteti parcurge login, register si sesizarea noua doar din tastatura
- puteti schimba rapid contrastul si marimea textului fara reload suplimentar
