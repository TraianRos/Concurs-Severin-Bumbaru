# Beginner Guide

## Ce este acest proiect

Acest proiect este o aplicatie mica pentru evenimente si inscrieri. Poti crea un eveniment si poti inscrie participanti.

Este potrivit pentru inceput in Python deoarece:

- are putine dependinte
- foloseste o baza de date locala
- codul este relativ usor de citit

## Ce trebuie sa ai instalat

- Python 3.12 sau mai nou
- pip
- un browser

SQLite este deja inclus de obicei in Python, deci nu trebuie instalat separat ca server.

## Cum verifici daca sunt instalate

```bash
python3 --version
pip --version
```

## Ce face fiecare tehnologie

- Python = limbajul principal
- Flask = primeste cererile si decide ce pagina se intoarce
- Flask-SQLAlchemy = ajuta codul Python sa lucreze cu baza de date
- SQLite = pastreaza datele in fisier local
- Jinja2 = construieste paginile HTML pe server

## Setup pas cu pas

### 1. Creeaza mediul virtual

```bash
python3 -m venv .venv
```

### 2. Activeaza mediul virtual

```bash
source .venv/bin/activate
```

### 3. Instaleaza dependintele

```bash
pip install -r requirements.txt
```

### 4. Creeaza baza de date si datele de test

```bash
python seed.py
```

### 5. Porneste aplicatia

```bash
python run.py
```

### 6. Deschide in browser

```text
http://localhost:5000
```

## Exista pas de compilare?

Nu. Python nu are aici un pas separat de compilare.

## Ce fisiere sa citesti primele

1. `run.py`
2. `app/__init__.py`
3. `app/routes/web.py`
4. `app/services/event_service.py`
5. `app/models/entities.py`

## Cum functioneaza pe scurt

1. Browser-ul cere o pagina.
2. Flask alege functia de ruta potrivita.
3. Ruta cheama service-ul.
4. Service-ul foloseste repository-urile.
5. Repository-urile citesc sau scriu in SQLite.
6. Flask trimite HTML inapoi in browser.

## Ce poti arata la prezentare

- lista de evenimente
- creare eveniment
- inscriere participant
- prevenirea unei inscrieri duplicate

## Ce sa retii

Acesta este unul dintre cele mai bune proiecte pentru a invata repede o aplicatie web completa in Python.

