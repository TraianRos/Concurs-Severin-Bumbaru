# RoomReserve Go

RoomReserve este o demonstratie pentru rezervarea salilor, scrisa in Go cu `net/http`. Este utila cand vrei un exemplu clar de server controlat manual, cu timeout-uri explicite si cu o regula de business foarte usor de explicat: nu permiti rezervari suprapuse.

## Daca esti la inceput

Citeste mai intai `BEGINNER_GUIDE.md`. Acolo ai:

- lista de programe pe care trebuie sa le ai instalate
- comenzile pentru creare baza de date
- pasii de rulare si, optional, de compilare
- explicatii simple despre ce face fiecare folder important

## Ce demonstreaza

- Arhitectura Go clasica cu `cmd/`, `internal/` si `web/`.
- Separare intre handler, service si repository.
- Utilizarea `database/sql` cu query-uri parametrizate.
- O combinatie de HTML server-rendered si un endpoint JSON mic.

## Rolul fiecarei tehnologii

- `Go` tine logica serverului si pune accent pe claritate si performanta.
- `net/http` gestioneaza serverul HTTP si rutele.
- `html/template` randareaza sigur HTML-ul.
- `SQLite` tine datele local.
- `JavaScript` este folosit doar pentru a reincarca sloturile disponibile in formular.

## Cum interactioneaza componentele

1. Browser-ul cere o pagina sau endpoint JSON.
2. Handler-ul Go citeste request-ul.
3. Handler-ul apeleaza `ReservationService`.
4. Service-ul valideaza input-ul si verifica sloturile deja rezervate.
5. Repository-ul citeste sau scrie in SQLite.
6. Handler-ul intoarce HTML sau JSON.

## Structura de fisiere

- `cmd/server/`
  - entrypoint-ul aplicatiei
- `internal/config/`
  - citeste configurarea
- `internal/model/`
  - defineste structurile de date
- `internal/repository/`
  - implementeaza accesul la SQLite
- `internal/service/`
  - tine regulile de business
- `internal/handler/`
  - transforma request-urile in raspunsuri
- `web/templates/`
  - paginile HTML
- `web/static/`
  - CSS si JavaScript pentru UI
- `db/`
  - schema si seed SQL

## Conventii folosite

- `cmd/` porneste aplicatia si construieste dependintele.
- `internal/` tine logica ce nu trebuie expusa in afara modulului.
- Handler-ul nu decide conflictele; service-ul decide.
- Repository-ul nu contine HTML si nu cunoaste detalii despre browser.
- Endpoint-ul JSON `/api/slots` este mic si specializat.

## Pornire

1. Creeaza baza SQLite si ruleaza `db/schema.sql`, apoi `db/seed.sql`.
2. Copiaza `.env.example` in `.env` daca vrei alte valori.
3. Porneste serverul:

```bash
go run ./cmd/server
```

## Flux demo

1. Vezi lista de sali.
2. Deschide formularul de rezervare.
3. Selecteaza sala si data.
4. Observa incarcare de sloturi disponibile.
5. Creeaza rezervarea.
6. Incearca acelasi slot pentru aceeasi sala si data si observa blocarea.

## Rute

- `GET /`
- `GET /rooms`
- `GET /reservations/new`
- `POST /reservations/new`
- `GET /api/slots`
- `GET /health`

## Cum il prezinti la concurs

- Spui ca este varianta potrivita cand vrei sa arati control clar asupra serverului.
- Evidentiezi timeouts-urile si `MaxHeaderBytes`.
- Explici conflictul de rezervare ca regula de business centrala.
