<?php

declare(strict_types=1);

namespace App\Controller;

abstract class BaseController
{
    protected function render(string $template, array $data = []): void
    {
        extract($data);
        $templatePath = __DIR__ . '/../../templates/' . $template . '.php';
        require __DIR__ . '/../../templates/layout.php';
    }

    protected function redirect(string $path, string $message): void
    {
        $_SESSION['flash'] = $message;
        header('Location: ' . $path);
        exit;
    }
}

