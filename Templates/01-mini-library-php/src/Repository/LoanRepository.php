<?php

declare(strict_types=1);

namespace App\Repository;

use App\Model\Loan;
use PDO;

final class LoanRepository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /** @return array<int, Loan> */
    public function all(): array
    {
        $statement = $this->connection->query(
            'SELECT l.id, b.title AS book_title, m.full_name AS member_name, l.loan_date, l.return_date, l.status
             FROM loans l
             JOIN books b ON b.id = l.book_id
             JOIN members m ON m.id = l.member_id
             ORDER BY l.loan_date DESC'
        );

        return array_map(
            fn (array $row): Loan => new Loan(
                (int) $row['id'],
                $row['book_title'],
                $row['member_name'],
                $row['loan_date'],
                $row['return_date'],
                $row['status']
            ),
            $statement->fetchAll()
        );
    }

    public function create(int $bookId, int $memberId, string $loanDate): void
    {
        $statement = $this->connection->prepare(
            'INSERT INTO loans (book_id, member_id, loan_date, status) VALUES (:book_id, :member_id, :loan_date, :status)'
        );

        $statement->execute([
            'book_id' => $bookId,
            'member_id' => $memberId,
            'loan_date' => $loanDate,
            'status' => 'borrowed',
        ]);
    }

    public function markReturned(int $loanId, string $returnDate): void
    {
        $statement = $this->connection->prepare(
            'UPDATE loans SET status = :status, return_date = :return_date WHERE id = :id AND status = :current_status'
        );

        $statement->execute([
            'status' => 'returned',
            'return_date' => $returnDate,
            'id' => $loanId,
            'current_status' => 'borrowed',
        ]);
    }

    public function findBorrowedBookId(int $loanId): ?int
    {
        $statement = $this->connection->prepare('SELECT book_id FROM loans WHERE id = :id AND status = :status');
        $statement->execute(['id' => $loanId, 'status' => 'borrowed']);
        $bookId = $statement->fetchColumn();

        return $bookId === false ? null : (int) $bookId;
    }

    public function activeCount(): int
    {
        $statement = $this->connection->prepare('SELECT COUNT(*) FROM loans WHERE status = :status');
        $statement->execute(['status' => 'borrowed']);

        return (int) $statement->fetchColumn();
    }
}

