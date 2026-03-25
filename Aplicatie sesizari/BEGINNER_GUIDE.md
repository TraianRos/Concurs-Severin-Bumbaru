# Beginner Guide

Acest fisier este scris intentionat simplu.

## Ce este proiectul

Este o aplicatie web in care:

- un cetatean se logheaza
- trimite o sesizare
- alege locul pe harta
- operatorul vede sesizarea
- operatorul schimba statusul sau o redirectioneaza
- cetateanul primeste notificare

## Ce trebuie sa ai instalat

- `Python 3.12+`
- `pip`
- `venv`
- un browser

Nu ai nevoie de MySQL sau PostgreSQL pentru aceasta versiune. Baza de date este un fisier SQLite.

## Cum verifici

```bash
python3 --version
pip --version
python3 -m venv --help
```

## Instalare pas cu pas

### 1. Intra in folder

```bash
cd "Aplicatie sesizari"
```

### 2. Creeaza mediul virtual

```bash
python3 -m venv .venv
```

### 3. Activeaza mediul virtual

```bash
source .venv/bin/activate
```

### 4. Instaleaza librariile

```bash
pip install -r requirements.txt
```

Librariile instalate din `requirements.txt` sunt:

- `Flask`
- `Flask-Login`
- `Flask-SQLAlchemy`
- `pytest`
- `waitress`

### 5. Creeaza baza de date si datele demo

```bash
python seed.py
```

### 6. Porneste serverul

```bash
python run.py
```

### 7. Deschide in browser

```text
http://127.0.0.1:5000
```

## Ce sa incerci prima data

1. intra cu utilizatorul `cetatean@oras.local`
2. creeaza o sesizare noua
3. alege un punct pe harta
4. delogheaza-te
5. intra cu `operator@oras.local`
6. schimba statusul sesizarii
7. intra din nou ca cetatean si verifica notificarile

## Ce face fiecare folder

- `app/models`
  - tabelele bazei de date
- `app/repositories`
  - locul unde se citesc si se scriu datele
- `app/services`
  - regulile aplicatiei
- `app/routes`
  - paginile si API-ul mic
- `app/templates`
  - HTML-ul
- `app/static`
  - CSS si JavaScript

## De unde incepi daca vrei sa citesti codul

1. `run.py`
2. `app/__init__.py`
3. `app/routes/web.py`
4. `app/services/incident_service.py`
5. `app/models/entities.py`

## Ce sa retii

- ruta = adresa, de exemplu `/incidents`
- service = locul unde se iau deciziile de business
- repository = stratul care vorbeste cu baza de date
- template = fisier HTML cu variabile Jinja

## De ce folosim `venv`, chiar pe o masina dedicata?

Pentru ca o masina dedicata nu inseamna automat si un singur proiect pe viata.

Avantajele reale sunt:

- nu amesteci librariile acestui proiect cu librariile sistemului
- poti avea versiuni clare si reproductibile
- daca strici ceva la pachete, stergi `.venv` si il refaci
- migrarea pe Raspberry Pi devine simpla: recreezi exact acelasi mediu din `requirements.txt`
- eviti sa instalezi global pachete care pot afecta alte proiecte sau unelte ale sistemului

Pe scurt:

- `requirements.txt` spune **ce pachete vrei**
- `.venv` este locul unde acele pachete sunt instalate local pentru proiectul curent

Nu este obligatoriu sa folosesti `venv`, dar este cea mai curata si sigura varianta pentru lucru serios, chiar si pe o masina dedicata.
