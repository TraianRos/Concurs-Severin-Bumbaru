# Database

## Tabele

### `books`

- `id` - cheie primara
- `title`
- `author`
- `category`
- `available_copies`
- `created_at`

### `members`

- `id` - cheie primara
- `full_name`
- `email`
- `created_at`

### `loans`

- `id` - cheie primara
- `book_id` - foreign key spre `books`
- `member_id` - foreign key spre `members`
- `loan_date`
- `return_date`
- `status`

## Relatii

- o carte poate avea mai multe imprumuturi
- un membru poate avea mai multe imprumuturi

## Query-uri utile

```sql
SELECT title, available_copies FROM books ORDER BY title;
```

```sql
SELECT l.id, b.title, m.full_name, l.status
FROM loans l
JOIN books b ON b.id = l.book_id
JOIN members m ON m.id = l.member_id;
```

```sql
SELECT COUNT(*) AS active_loans
FROM loans
WHERE status = 'borrowed';
```

