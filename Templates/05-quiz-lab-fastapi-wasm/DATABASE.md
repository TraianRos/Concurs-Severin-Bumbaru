# Database

## Tabele

### `quizzes`

- `id`
- `title`
- `topic`
- `created_at`

### `questions`

- `id`
- `quiz_id`
- `prompt`
- `correct_answer`
- `points`

### `submissions`

- `id`
- `quiz_id`
- `player_name`
- `score`
- `submitted_at`

## Query-uri utile

```sql
SELECT id, title, topic FROM quizzes ORDER BY title;
```

```sql
SELECT prompt, correct_answer, points
FROM questions
WHERE quiz_id = 1;
```

```sql
SELECT player_name, score
FROM submissions
WHERE quiz_id = 1
ORDER BY score DESC, submitted_at ASC;
```

