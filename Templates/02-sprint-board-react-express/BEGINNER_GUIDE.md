# Beginner Guide

## Ce este acest proiect

Acest proiect este un task manager mic. Utilizatorul vede proiecte si task-uri in browser, iar datele sunt pastrate intr-o baza PostgreSQL.

Este bun pentru studiu atunci cand vrei sa vezi cum lucreaza separat:

- partea vizibila in browser
- partea care proceseaza cererile
- baza de date

## Ce trebuie sa ai instalat

- Node.js 20 sau mai nou
- npm
- PostgreSQL
- un browser

## Cum verifici daca sunt instalate

```bash
node -v
npm -v
psql --version
```

## Ce face fiecare tehnologie

- React = construieste interfata din bucati mici numite componente
- Vite = porneste rapid frontend-ul in modul de dezvoltare
- Express = primeste cererile si trimite raspunsuri JSON
- PostgreSQL = pastreaza proiectele, task-urile si etichetele
- `pg` = biblioteca prin care Node vorbeste cu PostgreSQL

## Setup pas cu pas

### 1. Creeaza baza de date

```bash
psql -U postgres
```

In consola PostgreSQL:

```sql
CREATE DATABASE sprint_board;
\q
```

### 2. Creeaza tabelele

```bash
psql -U postgres -d sprint_board -f db/schema.sql
```

### 3. Adauga date de test

```bash
psql -U postgres -d sprint_board -f db/seed.sql
```

### 4. Configureaza backend-ul

```bash
cd backend
cp .env.example .env
npm install
```

Fisierul `.env` spune backend-ului:

- pe ce port sa porneasca
- unde este baza de date
- din ce adresa are voie frontend-ul sa trimita cereri

### 5. Porneste backend-ul

```bash
npm run dev
```

Backend-ul va porni, de regula, pe `http://localhost:4000`.

### 6. Configureaza frontend-ul

Intr-un al doilea terminal:

```bash
cd frontend
npm install
```

### 7. Porneste frontend-ul

```bash
npm run dev
```

Frontend-ul va porni, de regula, pe `http://localhost:5173`.

## Exista pas de compilare?

Da, pentru frontend exista si pas de build:

```bash
cd frontend
npm run build
```

Acest pas pregateste fisierele pentru o varianta finala, nu doar pentru dezvoltare.

Backend-ul Express nu are aici un pas separat de compilare.

## Ce fisiere sa citesti primele

1. `frontend/src/pages/DashboardPage.jsx`
2. `frontend/src/services/api.js`
3. `backend/src/app.js`
4. `backend/src/services/BoardService.js`
5. `backend/src/repositories/TaskRepository.js`

## Cum functioneaza pe scurt

1. Browser-ul deschide frontend-ul React.
2. React cere datele de la backend.
3. Backend-ul cauta datele in PostgreSQL.
4. Backend-ul trimite un raspuns JSON.
5. React afiseaza rezultatul.

## Ce poti arata la prezentare

- creare proiect
- creare task
- mutare task intre coloane
- stergere task
- legatura dintre React, Express si PostgreSQL

## Ce sa retii

Acesta este proiectul care te ajuta sa intelegi cel mai bine ideea de frontend separat de backend.

