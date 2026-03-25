# Beginner Guide

## Ce este acest proiect

Acest proiect este o aplicatie de quiz. Utilizatorul raspunde la intrebari, vede un scor calculat local in browser si apoi trimite rezultatul la server, care il verifica si il salveaza.

Este cel mai "special" proiect din repo, pentru ca foloseste si WebAssembly, dar poate fi inteles si fara sa stii deja WASM.

## Ce trebuie sa ai instalat

- Python 3.12 sau mai nou
- pip
- un browser
- optional: Emscripten daca vrei sa compilezi partea C++ in WebAssembly

## Cum verifici daca sunt instalate

```bash
python3 --version
pip --version
emcc --version
```

Daca `emcc` lipseste, nu este o problema pentru inceput. Aplicatia poate merge si cu fallback-ul JavaScript.

## Ce face fiecare tehnologie

- FastAPI = primeste cererile si trimite raspunsuri JSON
- SQLite = pastreaza quiz-urile si scorurile
- JavaScript = construieste quiz-ul in browser si trimite raspunsurile
- C++ = descrie algoritmul de scorare in forma sa canonica
- WebAssembly = permite rularea acelui algoritm in browser

## Setup pas cu pas

### 1. Creeaza mediul virtual

```bash
python3 -m venv .venv
```

### 2. Activeaza mediul virtual

```bash
source .venv/bin/activate
```

### 3. Instaleaza dependintele Python

```bash
pip install -r requirements.txt
```

### 4. Creeaza baza de date si datele de test

```bash
python seed.py
```

### 5. Porneste serverul

```bash
uvicorn app.main:app --reload
```

### 6. Deschide in browser

```text
http://localhost:8000
```

## Exista pas de compilare?

Pentru partea Python, nu. Pentru partea WebAssembly, da, dar este optional pentru prima intelegere.

### Compilare WASM optionala

```bash
cd wasm
chmod +x build.sh
./build.sh
```

Acest pas genereaza fisierele care permit browser-ului sa ruleze codul C++.

## Ce fisiere sa citesti primele

1. `app/main.py`
2. `app/routes/api.py`
3. `app/services/quiz_service.py`
4. `frontend/js/app.js`
5. `wasm/score.cpp`

## Cum functioneaza pe scurt

1. Frontend-ul cere lista de quiz-uri.
2. Utilizatorul alege un quiz si scrie raspunsuri.
3. Browser-ul calculeaza un scor local.
4. Raspunsurile sunt trimise la server.
5. Serverul recalculeaza scorul si il salveaza.
6. Frontend-ul afiseaza leaderboard-ul actualizat.

## Ce poti arata la prezentare

- alegerea unui quiz
- calculul scorului local
- trimiterea rezultatului la server
- diferenta dintre scorul local si verificarea pe server

## Ce sa retii

Nu trebuie sa pornesti direct de la acest proiect. El este mai util dupa ce ai inteles deja cum arata un backend simplu si cum arata o aplicatie web clasica.

