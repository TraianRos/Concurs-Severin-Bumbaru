# Database

## Tabele

### `projects`

- `id`
- `name`
- `description`
- `created_at`

### `tasks`

- `id`
- `project_id`
- `title`
- `description`
- `status`
- `due_date`
- `created_at`

### `labels`

- `id`
- `name`
- `color`

### `task_labels`

- `task_id`
- `label_id`

## Query-uri utile

```sql
SELECT id, name, description FROM projects ORDER BY created_at DESC;
```

```sql
SELECT t.title, t.status, p.name
FROM tasks t
JOIN projects p ON p.id = t.project_id;
```

```sql
SELECT l.name
FROM labels l
JOIN task_labels tl ON tl.label_id = l.id
WHERE tl.task_id = 1;
```

