<?php

declare(strict_types=1);

namespace App\Repository;

use App\Model\Member;
use PDO;

final class MemberRepository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /** @return array<int, Member> */
    public function all(): array
    {
        $statement = $this->connection->query('SELECT id, full_name, email FROM members ORDER BY full_name');

        return array_map(
            fn (array $row): Member => new Member((int) $row['id'], $row['full_name'], $row['email']),
            $statement->fetchAll()
        );
    }

    public function count(): int
    {
        return (int) $this->connection->query('SELECT COUNT(*) FROM members')->fetchColumn();
    }
}

