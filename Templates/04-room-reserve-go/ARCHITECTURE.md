# Architecture

## Vedere de ansamblu

Aplicatia urmeaza fluxul:

`Browser -> net/http handler -> ReservationService -> SQLiteRepository -> SQLite -> template/JSON -> Browser`

Este o arhitectura simpla si foarte explicita. Aproape fiecare pas poate fi urmarit dintr-un singur fisier.

## Straturi si responsabilitati

- `cmd/server/main.go`
  - configureaza conexiunea la baza de date
  - parseaza template-urile
  - configureaza timeouts-urile serverului
  - monteaza rutele
- `internal/handler`
  - citeste formulare si query params
  - produce HTML sau JSON
- `internal/service`
  - tine validarea si regula de evitare a suprapunerilor
- `internal/repository`
  - face query-uri parametrizate prin `database/sql`
- `internal/model`
  - defineste contractele interne de date

## Fluxuri importante

### Afisare dashboard

1. Request pe `/`
2. Handler-ul cere camerele si rezervarile curente
3. Service-ul ia datele din repository
4. Template-ul `home.html` le afiseaza

### Afisare sloturi disponibile

1. Browser-ul cere `/api/slots?room_id=...&date=...`
2. Handler-ul valideaza minim query params
3. Service-ul cere toate sloturile si sloturile deja rezervate
4. Service-ul filtreaza lista disponibila
5. Handler-ul intoarce JSON

### Creare rezervare

1. Formularul trimite `POST /reservations/new`
2. Handler-ul creeaza structura `Reservation`
3. Service-ul verifica input-ul si conflictul
4. Repository-ul scrie rezervarea in SQLite
5. Browser-ul este redirectionat pe dashboard

## Conventii arhitecturale

- HTTP config este explicita in `main.go`.
- Request-urile au timeout-uri pentru a evita serverul lasat in stari necontrolate.
- Service-ul este singurul loc care decide daca o rezervare este valida.
- `html/template` este folosit in loc de string concatenation.
- JSON-ul exista doar acolo unde ajuta clar formularul.

## Extensii usoare

- filtru dupa locatie
- anulare rezervare
- pagina dedicata pentru istoricul rezervarilor

