# SprintBoard React + Express

SprintBoard este o demonstratie cu frontend si backend separate. Scopul ei este sa arate cum arata un proiect web mai modern, unde browser-ul afiseaza o interfata React, iar API-ul Express expune date JSON din PostgreSQL.

## Daca esti la inceput

Citeste mai intai `BEGINNER_GUIDE.md`. Acolo ai:

- ce trebuie instalat
- pasii de pregatire pentru PostgreSQL
- cum pornesti backend-ul si frontend-ul in doua terminale
- explicatii simple despre cum comunica React si Express

## Ce demonstreaza

- Separare clara intre client si server.
- Consum de API REST dintr-un frontend React.
- Organizare pe straturi si in backend-ul Node.
- O baza relationala cu relatii simple intre proiecte, task-uri si etichete.

## Rolul fiecarei tehnologii

- `React` construieste interfata din componente reutilizabile.
- `Vite` este un tool de development si build pentru frontend.
- `Express` defineste API-ul HTTP si middleware-urile serverului.
- `Helmet` seteaza header-e de securitate utile pentru demo.
- `CORS` permite frontend-ului local sa comunice cu backend-ul local.
- `pg` este clientul PostgreSQL folosit de repository-uri.
- `PostgreSQL` pastreaza proiectele, task-urile si etichetele.

## Cum interactioneaza componentele

1. React incarca pagina si cere datele prin `fetch`.
2. Cererile trec prin `src/services/api.js`.
3. Backend-ul Express primeste request-ul pe o ruta `/api/...`.
4. Controller-ul extrage input-ul si il trimite in `BoardService`.
5. `BoardService` valideaza, normalizeaza si cere repository-urilor sa lucreze cu baza de date.
6. Repository-urile ruleaza query-uri parametrizate in PostgreSQL.
7. Backend-ul raspunde cu JSON, iar React rerandareaza componentele.

## Structura de fisiere

- `frontend/`
  - contine aplicatia React si tot ce tine de UI.
  - `src/pages/` tine paginile principale.
  - `src/components/` tine blocurile UI reutilizabile.
  - `src/services/` centralizeaza apelurile API.
  - `src/styles/` contine stilurile aplicatiei.
- `backend/`
  - contine API-ul Express.
  - `src/routes/` defineste endpoint-urile.
  - `src/controllers/` traduce cererea HTTP in apeluri de service.
  - `src/services/` tine logica de business.
  - `src/repositories/` executa SQL-ul.
  - `src/db/` tine conexiunea la PostgreSQL.
- `db/`
  - schema si seed pentru PostgreSQL.

## Conventii folosite

- Frontend-ul nu construieste URL-uri peste tot; toate request-urile pleaca din `api.js`.
- Componentele raman mici si au un singur rol principal.
- Backend-ul urmeaza fluxul `route -> controller -> service -> repository`.
- Validarea de business se face in service, nu direct in repository.
- Repository-urile folosesc numai query-uri parametrizate.
- Erorile API au format simplu, de tip `{"error":"..."}`.

## Pornire

### Backend

```bash
cd backend
cp .env.example .env
npm install
npm run dev
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Baza de date

1. Creeaza o baza `sprint_board`.
2. Ruleaza `db/schema.sql`.
3. Ruleaza `db/seed.sql`.

## Flux demo

1. Creezi un proiect nou.
2. Adaugi un task si alegi proiect, status si etichete.
3. Vezi task-ul in coloana potrivita.
4. Schimbi statusul si apoi stergi task-ul.

## API

- `GET /api/health`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/tasks`
- `POST /api/tasks`
- `PATCH /api/tasks/:id`
- `DELETE /api/tasks/:id`
- `GET /api/labels`

## Cum il prezinti la concurs

- Spui ca aceasta este varianta potrivita cand tema cere frontend dinamic.
- Evidentiezi separarea client/API/DB.
- Explici de ce centralizarea request-urilor in `api.js` si separarea in `service` si `repository` face codul mai clar.
