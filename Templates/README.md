# Workspace Pentru Antrenament Hackathon

Acest repo contine 5 schite de proiect web gandite pentru concursuri scurte in zona OOP, baze de date si tehnologii web.

## Daca esti la inceput

Inainte sa intri direct in cod, citeste [START-HERE.md](/mnt/d/Projects/ACIEE/anul 1/Concurs Severin Bumbaru/START-HERE.md). Acolo gasesti:

- explicatii simple despre ce inseamna frontend, backend si baza de date
- recomandarea cu ce proiect sa incepi
- link-uri catre ghidurile pentru incepatori din fiecare demonstratie

## Proiecte incluse

1. `01-mini-library-php` - PHP + MySQL/MariaDB
2. `03-event-hub-flask` - Flask + SQLite
3. `02-sprint-board-react-express` - React + Express + PostgreSQL
4. `04-room-reserve-go` - Go + SQLite
5. `05-quiz-lab-fastapi-wasm` - FastAPI + SQLite + C++ WebAssembly

## Cum sa folosesti repo-ul

- Incepe cu proiectele server-rendered daca vrei viteza de invatare.
- Continua cu React + Express pentru un stack separat frontend/backend.
- Foloseste Go si varianta WASM pentru comparatie si discutii tehnice.

## Ordine recomandata de studiu

1. `01-mini-library-php`
2. `03-event-hub-flask`
3. `02-sprint-board-react-express`
4. `04-room-reserve-go`
5. `05-quiz-lab-fastapi-wasm`

## Conventii comune

- Fiecare proiect are `README.md`, `ARCHITECTURE.md`, `DATABASE.md`, `.env.example` si scripturi SQL.
- Straturile sunt separate in `controller/handler`, `service`, `repository`, `model`.
- Input-ul este validat la marginea aplicatiei.
- Query-urile sunt parametrizate sau delegate ORM-ului.
- Mesajele de eroare sunt simple si nu expun stack trace-uri.

Vezi [setup-checklist](docs/setup-checklist.md) pentru runtime-uri si [stack-comparison](docs/stack-comparison.md) pentru recomandari.
