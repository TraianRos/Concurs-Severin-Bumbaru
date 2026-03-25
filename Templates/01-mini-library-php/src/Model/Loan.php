<?php

declare(strict_types=1);

namespace App\Model;

final class Loan
{
    public function __construct(
        public readonly int $id,
        public readonly string $bookTitle,
        public readonly string $memberName,
        public readonly string $loanDate,
        public readonly ?string $returnDate,
        public readonly string $status
    ) {
    }
}

