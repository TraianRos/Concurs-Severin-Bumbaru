# QuizLab FastAPI + WASM

QuizLab este o demonstratie comparativa: backend-ul FastAPI valideaza si persista datele, iar browser-ul calculeaza local un scor intermediar. Scopul nu este sa faci un sistem de quiz complet, ci sa intelegi ce inseamna separarea intre calcul local si validare server-side.

## Daca esti la inceput

Citeste mai intai `BEGINNER_GUIDE.md`. Acolo ai:

- setup-ul complet pentru Python
- explicatia simpla a rolului WebAssembly
- comenzile pentru rulare
- pasii optionali pentru compilarea partii C++

## Ce demonstreaza

- FastAPI ca backend JSON curat si rapid de scris.
- SQLite pentru persistenta usoara.
- Frontend static fara framework mare.
- C++ compilat in WebAssembly pentru o componenta tehnica speciala.
- Recalcularea scorului pe server, chiar daca browser-ul afiseaza un preview local.

## Rolul fiecarei tehnologii

- `FastAPI` defineste endpoint-urile si valideaza payload-urile prin Pydantic.
- `SQLite` stocheaza quiz-urile, intrebarile si submit-urile.
- `HTML + CSS + JavaScript` afiseaza UI-ul si colecteaza raspunsurile.
- `C++` descrie algoritmul de scorare in varianta canonica.
- `Emscripten` compileaza codul C++ in WebAssembly pentru browser.

## Cum interactioneaza componentele

1. Frontend-ul cere lista de quiz-uri de la FastAPI.
2. Utilizatorul deschide un quiz si completeaza raspunsurile.
3. Browser-ul calculeaza scorul local prin WASM sau prin fallback JS.
4. Frontend-ul trimite raspunsurile catre `/api/submissions`.
5. Backend-ul recalculeaza scorul pe baza raspunsurilor corecte din baza de date.
6. Backend-ul salveaza rezultatul si il trimite inapoi.
7. Frontend-ul actualizeaza leaderboard-ul.

## Structura de fisiere

- `app/main.py`
  - construieste FastAPI si monteaza frontend-ul static
- `app/routes/`
  - contine endpoint-urile API
- `app/services/`
  - tine logica de scorare si validare
- `app/repositories/`
  - citeste si scrie in SQLite
- `app/models/`
  - contine modelele Pydantic
- `frontend/`
  - contine pagina HTML, CSS-ul si JavaScript-ul UI
- `wasm/`
  - contine sursa C++ si scriptul de build
- `db/`
  - schema si seed SQL
- `tests/`
  - testele API de baza

## Conventii folosite

- Frontend-ul ramane simplu si nu depinde de framework-uri suplimentare.
- API-ul returneaza doar JSON.
- Backend-ul nu are incredere in scorul local afisat in browser.
- Repository-ul ascunde SQLite fata de service.
- Codul C++ ramane sursa canonica pentru partea de WASM.

## Pornire

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

Deschide apoi `http://localhost:8000`.

## Flux demo

1. Alegi un quiz.
2. Completezi raspunsurile.
3. Vezi scorul local in browser.
4. Trimiti submit-ul la server.
5. Vezi leaderboard-ul actualizat.

## API

- `GET /api/health`
- `GET /api/quizzes`
- `GET /api/quizzes/{id}`
- `POST /api/submissions`
- `GET /api/leaderboard`

## Observatie WASM

Codul C++ este sursa canonica pentru calculul scorului. Daca nu ai `emcc`, poti rula in continuare frontend-ul cu fallback-ul JavaScript deja inclus.

## Cum il prezinti la concurs

- Spui ca este exemplul "mai special", nu prima alegere pentru viteza.
- Evidentiezi ideea de scor local versus validare server-side.
- Arati cum un backend modern poate coexista cu un frontend foarte mic.
