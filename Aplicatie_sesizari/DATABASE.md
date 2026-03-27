# Database

## Tabele principale

### `users`

- `id`
- `full_name`
- `email`
- `password_hash`
- `role`
- `department_id`
- `created_at`

Rolul poate fi:

- `citizen`
- `operator`
- `dispatcher`
- `admin`

### `departments`

- `id`
- `name`
- `description`
- `contact_email`
- `created_at`

### `incident_categories`

- `id`
- `name`
- `description`
- `default_department_id`
- `created_at`

Fiecare categorie are un departament implicit. Asa se face prima redirectare automata.

### `incidents`

- `id`
- `title`
- `description`
- `address`
- `latitude`
- `longitude`
- `priority`
- `status`
- `created_by_id`
- `category_id`
- `suggested_department_id`
- `assigned_department_id`
- `created_at`
- `updated_at`

Toate sesizarile noi intra mai intai in `in_triere`. Departamentul ales de cetatean este pastrat separat in `suggested_department_id`, iar `assigned_department_id` este completat doar dupa triere.

### `incident_photos`

- `id`
- `incident_id`
- `stored_name`
- `original_name`
- `mime_type`
- `size_bytes`
- `width`
- `height`
- `is_pertinent`
- `created_at`

### `incident_updates`

- `id`
- `incident_id`
- `author_id`
- `message`
- `old_status`
- `new_status`
- `old_department_id`
- `new_department_id`
- `created_at`

Acest tabel pastreaza istoricul sesizarii.

### `incident_votes`

- `id`
- `incident_id`
- `user_id`
- `created_at`

Exista un singur vot pozitiv per pereche `(incident_id, user_id)`.

### `incident_reports`

- `id`
- `incident_id`
- `reporter_id`
- `reason`
- `details`
- `status`
- `reviewer_id`
- `resolution_note`
- `created_at`
- `reviewed_at`

Tabelul este folosit pentru raportari de tip duplicat, abuz/spam sau informatie incorecta.

### `incident_follows`

- `id`
- `incident_id`
- `user_id`
- `in_app_enabled`
- `email_enabled`
- `push_subscription_id`
- `created_at`
- `updated_at`

Un follow este configurat per sesizare si per utilizator.

### `web_push_subscriptions`

- `id`
- `user_id`
- `endpoint`
- `p256dh_key`
- `auth_key`
- `is_active`
- `created_at`
- `last_seen_at`

Acest tabel retine dispozitivele/browser-ele care pot primi notificari Web Push.

### `notifications`

- `id`
- `user_id`
- `incident_id`
- `message`
- `is_read`
- `created_at`

## Relatii

- un `department` are mai multi `users`
- un `department` poate primi mai multe `incidents`
- un `department` poate fi sugerat initial pentru un `incident`
- o `category` trimite implicit spre un `department`
- un `user` poate crea mai multe `incidents`
- un `incident` poate avea mai multe `incident_photos`
- un `incident` are mai multe `incident_updates`
- un `incident` poate avea mai multe `incident_votes`
- un `incident` poate avea mai multe `incident_reports`
- un `incident` poate avea mai multi `incident_follows`
- un `user` are mai multe `notifications`
- un `user` poate avea mai multe `web_push_subscriptions`

## De ce este buna aceasta organizare

- separa clar utilizatorii, incidentele si istoricul
- permite redirectare intre departamente fara sa pierzi cine a raportat
- permite notificari fara sa dublezi datele sesizarii
- tine separat engagement-ul (`vote`, `report`, `follow`) fata de fluxul operational
- pastreaza loc pentru extinderi ulterioare, cum ar fi moderare mai avansata sau mai multe dispozitive per follow
