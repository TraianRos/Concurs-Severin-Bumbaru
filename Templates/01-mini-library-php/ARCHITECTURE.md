# Architecture

## Vedere de ansamblu

Aplicatia urmeaza un model simplu de tip MVC-lite:

`Browser -> public/index.php -> Controller -> Service -> Repository -> MySQL -> Template -> Browser`

Nu exista framework extern, tocmai pentru ca fiecare piesa sa fie usor de citit si explicat.

## Responsabilitatea fiecarui strat

- `public/index.php`
  - incarca clasele prin autoloader
  - construieste dependintele
  - alege controller-ul in functie de ruta
- `Controller`
  - extrage input-ul din `$_GET` sau `$_POST`
  - apeleaza service-ul corect
  - decide redirect sau randare
- `Service`
  - valideaza campurile
  - verifica reguli de business, de exemplu stoc disponibil
  - coordoneaza mai multe repository-uri
- `Repository`
  - citeste si scrie date prin PDO
  - ascunde SQL-ul fata de restul aplicatiei
- `Model`
  - reprezinta entitatile in memorie
- `templates`
  - afiseaza datele deja pregatite

## Fluxuri importante

### Afisare lista de carti

1. Request pe `GET /books`
2. `BookController::index()`
3. `BookRepository::all()`
4. Rezultatul este trimis in `templates/books-list.php`

### Creare imprumut

1. Formularul trimite `POST /loans/create`
2. `LoanController::store()` preia datele
3. `LibraryService::createLoan()` valideaza cartea, membrul si data
4. `LoanRepository::create()` creeaza imprumutul
5. `BookRepository::decrementCopies()` actualizeaza stocul
6. Utilizatorul este redirectionat inapoi pe lista de imprumuturi

### Marcare retur

1. Request pe `POST /loans/{id}/return`
2. Service-ul cauta imprumutul activ
3. `LoanRepository::markReturned()` actualizeaza starea
4. `BookRepository::incrementCopies()` creste stocul

## Conventii arhitecturale

- Dependintele se construiesc o singura data in entrypoint.
- Service-ul poate folosi mai multe repository-uri intr-o singura operatie.
- SQL-ul nu apare nici in controller, nici in template.
- Template-urile nu decid logica de business.
- Healthcheck-ul este separat si foarte mic.

## Extensii usoare

- autentificare pentru bibliotecar
- cautare dupa titlu sau autor
- raport de imprumuturi intarziate

