# MiniLibrary PHP

MiniLibrary este o demonstratie mica pentru gestiunea cartilor si a imprumuturilor. Scopul ei nu este sa fie un produs complet, ci sa arate foarte clar cum se separa responsabilitatile intr-o aplicatie web clasica, server-rendered.

## Daca esti la inceput

Citeste mai intai `BEGINNER_GUIDE.md`. Acolo ai:

- dependintele explicate pe scurt
- pasii exacti de setup
- comenzile de pornire
- ordinea buna in care sa citesti fisierele

## Ce demonstreaza

- O aplicatie PHP fara framework mare, dar cu structura coerenta.
- Un flux CRUD complet: lista, creare si actualizare de stare.
- O separare explicita intre routare, controller, service, repository si template.
- Un exemplu simplu de baza de date relationala, usor de desenat la tabla.

## Rolul fiecarei tehnologii

- `PHP 8.2+` tine logica aplicatiei si serveste HTML-ul generat pe server.
- `PDO` este stratul de acces la baza de date si permite query-uri parametrizate.
- `MySQL/MariaDB` pastreaza cartile, membrii si imprumuturile.
- `HTML` descrie structura paginilor.
- `CSS` controleaza prezentarea si layout-ul responsive.
- `JavaScript` este minim si ramane optional; accentul aici este pe PHP si pe fluxul server-rendered.

## Cum interactioneaza componentele

1. Browser-ul cere o ruta, de exemplu `/books`.
2. `public/index.php` citeste metoda HTTP si ruta.
3. Router-ul simplu apeleaza controller-ul potrivit.
4. Controller-ul foloseste `LibraryService` pentru logica de business.
5. `LibraryService` foloseste repository-urile pentru operatii de citire sau scriere.
6. Repository-urile ruleaza query-uri PDO in baza de date.
7. Controller-ul trimite datele in template, iar template-ul genereaza HTML.

## Structura de fisiere

- `public/`
  - contine entrypoint-ul HTTP si asset-urile publice.
  - `index.php` este punctul de intrare pentru toate rutele.
- `src/Config/`
  - contine configurarea conexiunii la baza de date.
- `src/Controller/`
  - interpreteaza request-ul si decide ce raspuns intoarce.
- `src/Service/`
  - tine regulile de business si validarea importanta.
- `src/Repository/`
  - izoleaza complet interactiunea cu PDO.
- `src/Model/`
  - defineste obiectele de domeniu folosite in aplicatie.
- `templates/`
  - contine prezentarea HTML.
- `sql/`
  - contine schema si datele de seed.

## Conventii folosite

- Router-ul este explicit in `public/index.php`, pentru a fi usor de explicat.
- Controller-ul nu scrie SQL si nu contine reguli de business.
- Service-ul valideaza input-ul si decide daca o operatie este permisa.
- Repository-ul este singurul loc in care exista query-uri SQL.
- Template-urile afiseaza doar date pregatite deja de controller.
- Toate mesajele catre utilizator sunt scurte si usor de urmarit in demo.

## Pornire

1. Creeaza o baza de date noua, de exemplu `mini_library`.
2. Ruleaza `sql/schema.sql`.
3. Ruleaza `sql/seed.sql`.
4. Copiaza `.env.example` in `.env` si completeaza datele de conectare.
5. Porneste serverul local:

```bash
php -S localhost:8000 -t public
```

## Flux demo

1. Deschide dashboard-ul.
2. Vezi sumarul: carti, membri, imprumuturi active.
3. Intra pe lista de carti si adauga o carte noua.
4. Intra pe lista de imprumuturi si creeaza un imprumut.
5. Marcheaza un retur si observa actualizarea stocului.

## Rute

- `GET /`
- `GET /books`
- `GET /books/create`
- `POST /books/create`
- `GET /loans`
- `GET /loans/create`
- `POST /loans/create`
- `POST /loans/{id}/return`
- `GET /api/health`

## Cum il prezinti la concurs

- Spui ca este varianta clasica pentru un CRUD cu accent pe OOP si SQL.
- Desenezi fluxul `request -> controller -> service -> repository -> DB`.
- Explici de ce server-rendering-ul scade complexitatea si viteza de setup.
