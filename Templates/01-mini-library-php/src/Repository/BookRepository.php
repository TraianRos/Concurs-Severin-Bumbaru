<?php

declare(strict_types=1);

namespace App\Repository;

use App\Model\Book;
use PDO;

final class BookRepository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /** @return array<int, Book> */
    public function all(): array
    {
        $statement = $this->connection->query('SELECT id, title, author, category, available_copies FROM books ORDER BY title');

        return array_map(
            fn (array $row): Book => new Book(
                (int) $row['id'],
                $row['title'],
                $row['author'],
                $row['category'],
                (int) $row['available_copies']
            ),
            $statement->fetchAll()
        );
    }

    public function find(int $id): ?Book
    {
        $statement = $this->connection->prepare('SELECT id, title, author, category, available_copies FROM books WHERE id = :id');
        $statement->execute(['id' => $id]);
        $row = $statement->fetch();

        if (!$row) {
            return null;
        }

        return new Book(
            (int) $row['id'],
            $row['title'],
            $row['author'],
            $row['category'],
            (int) $row['available_copies']
        );
    }

    public function create(string $title, string $author, string $category, int $copies): void
    {
        $statement = $this->connection->prepare(
            'INSERT INTO books (title, author, category, available_copies) VALUES (:title, :author, :category, :copies)'
        );

        $statement->execute([
            'title' => $title,
            'author' => $author,
            'category' => $category,
            'copies' => $copies,
        ]);
    }

    public function decrementCopies(int $id): void
    {
        $statement = $this->connection->prepare(
            'UPDATE books SET available_copies = available_copies - 1 WHERE id = :id AND available_copies > 0'
        );
        $statement->execute(['id' => $id]);
    }

    public function incrementCopies(int $id): void
    {
        $statement = $this->connection->prepare('UPDATE books SET available_copies = available_copies + 1 WHERE id = :id');
        $statement->execute(['id' => $id]);
    }

    public function count(): int
    {
        return (int) $this->connection->query('SELECT COUNT(*) FROM books')->fetchColumn();
    }
}

