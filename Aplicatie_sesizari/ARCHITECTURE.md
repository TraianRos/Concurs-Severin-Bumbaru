# Architecture

## Vedere de ansamblu

Aplicatia urmeaza doua fluxuri simple:

- fluxul HTML: `Browser -> Flask route -> Service -> Repository -> SQLite -> Jinja -> Browser`
- fluxul JSON: `Browser -> Flask API route -> Service -> Repository -> SQLite -> JSON -> Browser`

Partea HTML este principala. API-ul exista doar pentru lucrurile mici care au sens in browser:

- marker-ele de pe harta
- contorul de notificari necitite

## Rolul fiecarui strat

- `app/routes`
  - primeste request-ul si alege ce service trebuie apelat
- `app/services`
  - verifica reguli ca: campuri obligatorii, roluri, statusuri valide, notificari
- `app/repositories`
  - ascunde accesul la baza de date
- `app/models`
  - defineste tabelele si relatiile
- `app/templates`
  - afiseaza datele pentru utilizator
- `app/static/js/app.js`
  - porneste harta si cere JSON pentru markere/notificari

## Fluxuri importante

### 1. Creare sesizare

1. cetateanul deschide `/incidents/new`
2. completeaza formularul si alege punctul pe harta
3. browser-ul trimite formularul la Flask
4. `IncidentService.create_incident()` valideaza datele
5. repository-ul creeaza sesizarea si primul update
6. se creeaza notificari pentru staff-ul relevant
7. utilizatorul este dus pe pagina de detaliu

### 2. Lista + harta

1. utilizatorul deschide `/incidents`
2. Flask intoarce HTML-ul listei si filtrele
3. JavaScript mai cere `GET /api/incidents/markers`
4. API-ul intoarce aceleasi sesizari, dar in format simplu pentru harta
5. Leaflet pune pin-urile pe OpenStreetMap

### 3. Actualizare operator

1. operatorul deschide pagina unei sesizari
2. trimite status nou, departament si mesaj
3. `IncidentService.update_incident()` verifica daca schimbarea este valida
4. service-ul salveaza update-ul in istoric
5. service-ul creeaza notificare pentru cetatean
6. cetateanul vede contorul de notificari actualizat

## De ce este arhitectura buna pentru echipa

- nu aveti frontend si backend separate in doua proiecte
- fiecare fisier are un rol clar
- este usor de explicat la prezentare
- puteti adauga functii noi fara sa stricati tot

## Extensii naturale

- upload foto pentru sesizare
- vot sau follow pentru alte sesizari
- raportare duplicate
- trimitere email pe langa notificarile interne
- export CSV pentru operatori
