# Database

## Tabele

### `rooms`

- `id`
- `name`
- `capacity`
- `location`

### `time_slots`

- `id`
- `start_time`
- `end_time`

### `reservations`

- `id`
- `room_id`
- `reserved_by`
- `slot_id`
- `reservation_date`
- `purpose`
- `created_at`

## Query-uri utile

```sql
SELECT name, capacity, location FROM rooms ORDER BY name;
```

```sql
SELECT r.reservation_date, rm.name, ts.start_time, ts.end_time
FROM reservations r
JOIN rooms rm ON rm.id = r.room_id
JOIN time_slots ts ON ts.id = r.slot_id;
```

```sql
SELECT slot_id
FROM reservations
WHERE room_id = 1 AND reservation_date = '2026-04-08';
```

