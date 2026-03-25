# Database

## Tabele

### `events`

- `id`
- `title`
- `location`
- `start_date`
- `seats`
- `created_at`

### `attendees`

- `id`
- `full_name`
- `email`
- `created_at`

### `registrations`

- `id`
- `event_id`
- `attendee_id`
- `registered_at`
- `status`

## Relatii

- un eveniment poate avea mai multe inscrieri
- un participant poate aparea la mai multe evenimente
- `registrations` leaga participantii de evenimente

## Query-uri utile

```sql
SELECT title, location, start_date FROM events ORDER BY start_date;
```

```sql
SELECT e.title, COUNT(r.id) AS seats_taken
FROM events e
LEFT JOIN registrations r ON r.event_id = e.id
GROUP BY e.id;
```

```sql
SELECT a.full_name, a.email
FROM attendees a
JOIN registrations r ON r.attendee_id = a.id
WHERE r.event_id = 1;
```

