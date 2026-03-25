# Architecture

## Vedere de ansamblu

Aplicatia are doua fluxuri paralele:

- fluxul de date: `Frontend -> FastAPI -> SQLite`
- fluxul de calcul local: `Frontend -> WASM/JS fallback -> preview score`

Fluxul complet este:

`Browser -> app.js -> FastAPI route -> QuizService -> QuizRepository -> SQLite -> JSON -> Browser`

## Backend

- `app/main.py`
  - creeaza aplicatia FastAPI
  - initializeaza baza de date
  - serveste frontend-ul static
- `app/routes/api.py`
  - expune endpoint-urile JSON
- `app/services/quiz_service.py`
  - recalculeaza scorul
  - valideaza numele jucatorului si quiz-ul selectat
- `app/repositories/quiz_repository.py`
  - ruleaza query-uri parametrizate in SQLite
- `app/models/schemas.py`
  - descrie payload-ul primit de la frontend

## Frontend

- `frontend/index.html`
  - shell-ul paginii
- `frontend/js/app.js`
  - cere quiz-uri
  - construieste formularul dinamic
  - afiseaza leaderboard-ul
  - calculeaza preview-ul local
- `frontend/assets/styles.css`
  - stilurile UI

## WASM

- `wasm/score.cpp`
  - defineste functia de scorare
- `wasm/build.sh`
  - produce artefactele necesare pentru browser
- fallback-ul JavaScript
  - pastreaza demo-ul utilizabil si fara Emscripten

## Fluxuri importante

### Incarcarea quiz-urilor

1. Browser-ul cere `/api/quizzes`
2. Backend-ul citeste tabela `quizzes`
3. Frontend-ul afiseaza lista de quiz-uri

### Afisarea unui quiz

1. Browser-ul cere `/api/quizzes/{id}`
2. Backend-ul intoarce quiz-ul si intrebarile
3. Frontend-ul construieste formularul dinamic

### Trimiterea unui rezultat

1. Utilizatorul apasa submit
2. Frontend-ul calculeaza local un preview
3. Payload-ul este trimis la `/api/submissions`
4. Backend-ul recalculeaza scorul din raspunsurile corecte
5. Backend-ul scrie in tabela `submissions`
6. Frontend-ul reincarca leaderboard-ul

## Conventii arhitecturale

- Serverul nu are incredere in browser pentru scorul final.
- Endpoint-urile sunt mici si specializate.
- SQLite este ascuns in repository.
- FastAPI tine validarea de forma prin Pydantic, iar service-ul tine regula de business.
- Frontend-ul ramane deliberat mic, ca sa se vada clar ideea WASM.

## Extensii usoare

- cronometru per quiz
- categorii multiple
- pagina de statistici per jucator

