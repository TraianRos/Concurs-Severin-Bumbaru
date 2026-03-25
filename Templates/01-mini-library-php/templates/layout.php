<?php

declare(strict_types=1);

$flashMessage = $_SESSION['flash'] ?? null;
unset($_SESSION['flash']);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($pageTitle ?? 'MiniLibrary', ENT_QUOTES, 'UTF-8') ?></title>
    <link rel="stylesheet" href="/assets/styles.css">
</head>
<body>
    <header class="site-header">
        <div>
            <p class="eyebrow">MiniLibrary</p>
            <h1><?= htmlspecialchars($pageTitle ?? 'MiniLibrary', ENT_QUOTES, 'UTF-8') ?></h1>
        </div>
        <nav class="site-nav">
            <a href="/">Dashboard</a>
            <a href="/books">Books</a>
            <a href="/loans">Loans</a>
        </nav>
    </header>

    <main class="page-shell">
        <?php if ($flashMessage): ?>
            <p class="flash-message"><?= htmlspecialchars($flashMessage, ENT_QUOTES, 'UTF-8') ?></p>
        <?php endif; ?>

        <?php require $templatePath; ?>
    </main>
</body>
</html>

