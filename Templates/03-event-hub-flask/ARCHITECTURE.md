# Architecture

## Vedere de ansamblu

Aplicatia urmeaza fluxul:

`Browser -> Flask route -> EventService -> repositories -> SQLAlchemy -> SQLite -> Jinja -> Browser`

Este o arhitectura foarte buna pentru demo-uri in care vrei sa arati clar backend, template-uri si date relationale, fara sa introduci si un frontend separat.

## Straturi si responsabilitati

- `run.py`
  - porneste serverul local
- `app/__init__.py`
  - aplica configurarea si inregistreaza blueprint-ul
- `routes/web.py`
  - defineste endpoint-urile si HTTP flow-ul
- `services/event_service.py`
  - valideaza formularul
  - verifica locurile disponibile
  - blocheaza inscrierea duplicata
- `repositories/*`
  - encapsuleaza citirea si scrierea prin ORM
- `models/entities.py`
  - defineste entitatile si relatiile dintre ele
- `templates/*`
  - genereaza HTML-ul final

## Fluxuri importante

### Afisare homepage

1. Browser-ul cere `/`
2. Ruta `home()` cere date de la `EventService`
3. Service-ul foloseste `EventRepository.upcoming()`
4. Template-ul `home.html` afiseaza evenimentele

### Creare eveniment

1. Browser-ul trimite `POST /events/new`
2. Ruta apeleaza `EventService.create_event()`
3. Service-ul valideaza titlu, locatie, data si numar de locuri
4. `EventRepository.create()` persista entitatea
5. Utilizatorul este redirectionat catre lista de evenimente

### Inscriere participant

1. Browser-ul trimite `POST /events/<id>/register`
2. Service-ul cauta evenimentul si participantul
3. Daca participantul nu exista, il creeaza
4. Verifica locurile ramase si inscrierea duplicata
5. Creeaza randul din `registrations`

## Conventii arhitecturale

- Aplicatia foloseste app factory pentru a permite configurare usoara si teste.
- Dependinta `db` este centralizata in `extensions.py`.
- Rutele nu cunosc detalii despre ORM.
- Service-ul este singurul loc in care sunt exprimate regulile de business.
- Template-urile doar afiseaza datele primite.

## Extensii usoare

- pagina de administrare pentru stergere evenimente
- filtru dupa locatie
- export lista participanti

