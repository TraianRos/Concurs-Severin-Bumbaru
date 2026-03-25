# Beginner Guide

## Ce este acest proiect

Acest proiect este o aplicatie mica pentru rezervarea salilor. Poti vedea ce sali exista, poti alege o data si un interval orar si poti crea o rezervare.

Este util daca vrei sa vezi:

- cum porneste un server web in Go
- cum se face legatura intre formular si baza de date
- cum blochezi o rezervare care se suprapune peste alta

## Ce trebuie sa ai instalat

- Go 1.22 sau mai nou
- SQLite sau macar fisierul bazei de date creat in alt mod
- un browser

## Cum verifici daca sunt instalate

```bash
go version
sqlite3 --version
```

Daca nu ai comanda `sqlite3`, proiectul poate fi totusi studiat, dar pentru un demo complet este mai comod sa o ai.

## Ce face fiecare tehnologie

- Go = limbajul principal al aplicatiei
- `net/http` = partea din Go care primeste cereri web
- `html/template` = partea care construieste paginile HTML
- SQLite = baza de date locala
- JavaScript = ajuta formularul sa incarce sloturile disponibile

## Setup pas cu pas

### 1. Creeaza baza de date

```bash
sqlite3 room_reserve.db < db/schema.sql
```

### 2. Adauga date de test

```bash
sqlite3 room_reserve.db < db/seed.sql
```

### 3. Configureaza aplicatia

```bash
cp .env.example .env
```

In `.env` poti schimba:

- portul pe care porneste serverul
- numele fisierului bazei de date

### 4. Ruleaza aplicatia

```bash
go run ./cmd/server
```

### 5. Deschide in browser

```text
http://localhost:8080
```

## Exista pas de compilare?

Da. Daca vrei un fisier executabil separat, poti folosi:

```bash
go build -o room-reserve ./cmd/server
```

Dupa aceea rulezi:

```bash
./room-reserve
```

## Ce fisiere sa citesti primele

1. `cmd/server/main.go`
2. `internal/handler/handler.go`
3. `internal/service/reservation_service.go`
4. `internal/repository/sqlite_repository.go`
5. `web/templates/`

## Cum functioneaza pe scurt

1. Browser-ul cere o pagina.
2. Serverul Go vede ce pagina sau ce endpoint a fost cerut.
3. Daca e nevoie de date, service-ul intreaba repository-ul.
4. Repository-ul cauta datele in SQLite.
5. Serverul trimite HTML sau JSON inapoi.

## Ce poti arata la prezentare

- lista de sali
- formularul de rezervare
- incarcare de sloturi disponibile
- blocarea unui conflict de rezervare

## Ce sa retii

Acest proiect este bun daca vrei sa arati clar cum functioneaza un server web, fara sa depinzi de un framework mare.

