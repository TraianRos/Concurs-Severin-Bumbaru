<?php

declare(strict_types=1);

namespace App\Model;

final class Book
{
    public function __construct(
        public readonly int $id,
        public readonly string $title,
        public readonly string $author,
        public readonly string $category,
        public readonly int $availableCopies
    ) {
    }
}

