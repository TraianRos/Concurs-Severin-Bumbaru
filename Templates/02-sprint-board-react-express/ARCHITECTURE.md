# Architecture

## Vedere de ansamblu

Aplicatia este impartita in doua procese logice:

- frontend React pentru UI
- backend Express pentru API

Fluxul complet este:

`Browser -> React components -> api.js -> Express routes -> controllers -> BoardService -> repositories -> PostgreSQL -> JSON -> React`

## Frontend

- `App.jsx`
  - shell-ul aplicatiei
- `DashboardPage.jsx`
  - incarca proiecte, task-uri si etichete
  - coordoneaza submit-ul formularelor
- `ProjectList.jsx`
  - afiseaza proiectele si permite creare de proiect
- `TaskForm.jsx`
  - construieste payload-ul pentru creare task
- `TaskBoard.jsx`
  - grupeaza task-urile pe status
- `src/services/api.js`
  - singurul loc in care exista apeluri `fetch`

## Backend

- `app.js`
  - configureaza middleware-urile si monteaza rutele
- `routes/*`
  - leaga endpoint-urile de controllere
- `controllers/*`
  - citesc `req.body` sau `req.params`
  - intorc raspunsurile HTTP
- `services/BoardService.js`
  - valideaza statusuri, campuri si id-uri
  - coordoneaza operatii care ating mai multe tabele
- `repositories/*`
  - contin query-uri SQL parametrizate
- `db/pool.js`
  - tine conexiunea la PostgreSQL

## Fluxuri importante

### Incarcarea dashboard-ului

1. React porneste `loadData()`
2. `api.js` cere `/projects`, `/tasks` si `/labels`
3. Express raspunde cu JSON
4. `DashboardPage` actualizeaza state-ul si reface UI-ul

### Crearea unui task

1. `TaskForm` construieste payload-ul
2. `api.createTask()` trimite `POST /api/tasks`
3. Controller-ul apeleaza `BoardService.createTask()`
4. Service-ul valideaza si cere `TaskRepository.create()`
5. Repository-ul scrie in `tasks` si `task_labels`
6. Frontend-ul reincarca datele

### Schimbarea statusului

1. Utilizatorul selecteaza alt status in `TaskBoard`
2. Frontend-ul trimite `PATCH /api/tasks/:id`
3. Service-ul valideaza noul status
4. Repository-ul actualizeaza randul din PostgreSQL

## Conventii arhitecturale

- API-ul expune doar JSON, nu HTML.
- Frontend-ul nu contine SQL si nu stie detalii despre PostgreSQL.
- Backend-ul nu cunoaste detalii de prezentare din React.
- Fiecare strat poate fi explicat separat.
- Rutele si controllerele raman subtiri, iar service-ul tine logica utila.

## Extensii usoare

- filtrare task-uri dupa proiect
- cautare dupa titlu
- autentificare simpla pentru membrii echipei

