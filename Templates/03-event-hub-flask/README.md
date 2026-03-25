# EventHub Flask

EventHub este o demonstratie server-rendered pentru evenimente si inscrieri. Este gandita ca exemplu echilibrat intre claritatea codului Python si structura unei aplicatii web cu modele, relatii si validare.

## Daca esti la inceput

Citeste mai intai `BEGINNER_GUIDE.md`. Acolo gasesti:

- pasii de instalare pentru Python
- crearea mediului virtual
- comenzile exacte pentru rulare
- o explicatie simpla a modului in care Flask lucreaza cu SQLite

## Ce demonstreaza

- App factory in Flask.
- Organizare pe blueprint, service, repository si model.
- Utilizarea unui ORM pentru relatii intre entitati.
- Un flux simplu de inscriere la eveniment.

## Rolul fiecarei tehnologii

- `Python 3.12+` tine logica aplicatiei si ofera un cod scurt si clar.
- `Flask` gestioneaza request-urile si raspunsurile HTTP.
- `Flask-SQLAlchemy` leaga modelele Python de SQLite.
- `SQLite` pastreaza datele local, fara setup complex.
- `Jinja2` randareaza paginile HTML pe server.

## Cum interactioneaza componentele

1. Browser-ul cere o pagina, de exemplu `/events`.
2. Blueprint-ul Flask alege functia de ruta potrivita.
3. Ruta apeleaza `EventService`.
4. `EventService` valideaza datele si foloseste repository-urile.
5. Repository-urile citesc sau scriu prin SQLAlchemy.
6. Ruta trimite datele in template-ul Jinja.
7. Template-ul afiseaza rezultatul in browser.

## Structura de fisiere

- `run.py`
  - punctul de pornire pentru serverul local
- `seed.py`
  - initializeaza baza de date si seed-ul
- `app/__init__.py`
  - construieste aplicatia prin app factory
- `app/config.py`
  - tine configurarea de baza
- `app/extensions.py`
  - defineste extensiile comune, de exemplu `db`
- `app/models/`
  - tine entitatile SQLAlchemy
- `app/repositories/`
  - ascunde accesul la baza de date
- `app/services/`
  - tine regulile de business
- `app/routes/`
  - defineste rutele HTML si healthcheck-ul
- `app/templates/`
  - contine paginile server-rendered
- `app/static/`
  - contine stilurile
- `tests/`
  - contine testul minim al fluxului principal

## Conventii folosite

- Rutele raman subtiri si cheama un singur service.
- Service-ul valideaza si coordoneaza mai multe repository-uri.
- Repository-urile ascund ORM-ul fata de restul codului.
- Seed-ul este separat de logica de request.
- Template-urile nu fac calcule importante.

## Instalare

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python run.py
```

## Flux demo

1. Deschide pagina principala.
2. Vezi evenimentele existente.
3. Creeaza un eveniment nou.
4. Intra pe detaliu si inscrie un participant.
5. Repeta inscrierea cu acelasi email si observa validarea.

## Rute

- `GET /`
- `GET /events`
- `GET /events/new`
- `POST /events/new`
- `GET /events/<id>`
- `POST /events/<id>/register`
- `GET /health`

## Cum il prezinti la concurs

- Spui ca este varianta Python server-rendered, cu setup foarte rapid.
- Explici relatia `events -> registrations <- attendees`.
- Evidentiezi app factory-ul si avantajul de a separa blueprint-ul de service.
