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
- `assigned_department_id`
- `created_at`
- `updated_at`

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
- o `category` trimite implicit spre un `department`
- un `user` poate crea mai multe `incidents`
- un `incident` are mai multe `incident_updates`
- un `user` are mai multe `notifications`

## De ce este buna aceasta organizare

- separa clar utilizatorii, incidentele si istoricul
- permite redirectare intre departamente fara sa pierzi cine a raportat
- permite notificari fara sa dublezi datele sesizarii
- poate fi extinsa usor cu poze, voturi sau comentarii
