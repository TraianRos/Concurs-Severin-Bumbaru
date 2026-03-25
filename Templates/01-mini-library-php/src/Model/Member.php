<?php

declare(strict_types=1);

namespace App\Model;

final class Member
{
    public function __construct(
        public readonly int $id,
        public readonly string $fullName,
        public readonly string $email
    ) {
    }
}

