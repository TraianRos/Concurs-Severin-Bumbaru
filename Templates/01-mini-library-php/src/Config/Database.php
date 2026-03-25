<?php

declare(strict_types=1);

namespace App\Config;

use PDO;
use PDOException;

final class Database
{
    public static function connect(string $projectRoot): PDO
    {
        $env = self::loadEnv($projectRoot . '/.env');

        $host = $env['DB_HOST'] ?? '127.0.0.1';
        $port = $env['DB_PORT'] ?? '3306';
        $name = $env['DB_NAME'] ?? 'mini_library';
        $user = $env['DB_USER'] ?? 'root';
        $pass = $env['DB_PASS'] ?? '';

        $dsn = sprintf('mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4', $host, $port, $name);

        try {
            return new PDO($dsn, $user, $pass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]);
        } catch (PDOException $exception) {
            throw new PDOException('Database connection failed.');
        }
    }

    private static function loadEnv(string $path): array
    {
        if (!is_file($path)) {
            return [];
        }

        $rows = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        $values = [];

        foreach ($rows as $row) {
            if (str_starts_with(trim($row), '#') || !str_contains($row, '=')) {
                continue;
            }

            [$key, $value] = explode('=', $row, 2);
            $values[trim($key)] = trim($value);
        }

        return $values;
    }
}

