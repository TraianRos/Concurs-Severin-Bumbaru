# Architecture

## Vedere de ansamblu

Aplicatia urmeaza doua fluxuri simple:

- fluxul HTML: `Browser -> Flask route -> Service -> Repository -> SQLite -> Jinja -> Browser`
- fluxul JSON: `Browser -> Flask API route -> Service -> Repository -> SQLite -> JSON -> Browser`

Partea HTML este principala. API-ul exista doar pentru lucrurile mici care au sens in browser:

- marker-ele de pe harta
- contorul de notificari necitite
- abonarea dispozitivului curent pentru Web Push

## Rolul fiecarui strat

- `app/routes`
  - primeste request-ul si alege ce service trebuie apelat
- `app/services`
  - verifica reguli ca: campuri obligatorii, roluri, statusuri valide, notificari, vote/report/follow
- `app/repositories`
  - ascunde accesul la baza de date
- `app/models`
  - defineste tabelele si relatiile
- `app/templates`
  - afiseaza datele pentru utilizator
- `app/static/js/app.js`
  - porneste harta si cere JSON pentru markere, notificari si Web Push

## Fluxuri importante

### 1. Creare sesizare

1. cetateanul deschide `/incidents/new`
2. completeaza formularul si alege punctul pe harta
3. browser-ul trimite formularul la Flask
4. `IncidentService.create_incident()` valideaza datele
5. repository-ul creeaza sesizarea si primul update
6. se creeaza notificari pentru staff-ul relevant
7. utilizatorul este dus pe pagina de detaliu
8. autorul devine automat follower intern pentru propria sesizare

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
5. service-ul notifica followerii sesizarii prin canalele alese
6. cetateanul vede contorul de notificari actualizat

### 4. Engagement pe sesizare

1. utilizatorul deschide pagina de detaliu
2. poate vota, urmari sau raporta sesizarea
3. `IncidentService` aplica regulile de business:
   - autorul nu isi poate vota sau raporta propriul caz
   - exista un singur vot pozitiv per utilizator
   - exista cel mult un raport deschis per utilizator si sesizare
4. `NotificationDispatchService` livreaza best-effort:
   - notificare interna
   - email
   - Web Push pe dispozitivul curent
5. esecurile de email/push se logheaza separat, fara sa rupa fluxul principal

## Accesibilitate in arhitectura

Aplicatia trateaza accesibilitatea ca o combinatie intre:

- HTML semantic in `app/templates`
- preferinte vizuale persistente in `app/static/js/app.js`
- token-uri CSS si focus vizibil in `app/static/styles.css`
- validare de baza si mesaje clare in `app/services`

Concret:

- formularul de sesizare poate prelua locatia dispozitivului si permite selectarea punctului direct pe harta
- panoul de accesibilitate salveaza local preferintele pentru marime text, contrast si miscare
- formularele importante afiseaza sumar de erori si marcheaza campurile invalide
- hartile raman elemente ajutatoare; informatia esentiala exista si in text
- notificarile, mesajele flash si statusurile foto sunt expuse in regiuni potrivite pentru screen reader
- actiunile de engagement sunt inline, fara modal-uri, pentru navigare mai predictibila cu tastatura si screen reader
- exista un `live region` global pentru anunturi de stare generate in browser

## De ce este arhitectura buna pentru echipa

- nu aveti frontend si backend separate in doua proiecte
- fiecare fisier are un rol clar
- este usor de explicat la prezentare
- puteti adauga functii noi fara sa stricati tot

## Extensii naturale

- worker separat pentru email si Web Push
- moderare mai avansata pentru duplicate
- agregare follow pe mai multe dispozitive simultan
- export CSV pentru operatori
