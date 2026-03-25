<?php

declare(strict_types=1);

use App\Config\Database;
use App\Controller\BookController;
use App\Controller\HomeController;
use App\Controller\LoanController;
use App\Repository\BookRepository;
use App\Repository\LoanRepository;
use App\Repository\MemberRepository;
use App\Service\LibraryService;

session_start();

spl_autoload_register(function (string $className): void {
    $prefix = 'App\\';
    if (!str_starts_with($className, $prefix)) {
        return;
    }

    $relative = str_replace('\\', '/', substr($className, strlen($prefix)));
    $path = dirname(__DIR__) . '/src/' . $relative . '.php';

    if (is_file($path)) {
        require $path;
    }
});

$projectRoot = dirname(__DIR__);
$connection = Database::connect($projectRoot);

$bookRepository = new BookRepository($connection);
$memberRepository = new MemberRepository($connection);
$loanRepository = new LoanRepository($connection);
$libraryService = new LibraryService($bookRepository, $memberRepository, $loanRepository);

$homeController = new HomeController($libraryService);
$bookController = new BookController($bookRepository, $libraryService);
$loanController = new LoanController($loanRepository, $bookRepository, $memberRepository, $libraryService);

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';

// Routing stays explicit so the user can present it quickly during the contest.
switch (true) {
    case $method === 'GET' && $path === '/':
        $homeController->index();
        break;
    case $method === 'GET' && $path === '/api/health':
        $homeController->health();
        break;
    case $method === 'GET' && $path === '/books':
        $bookController->index();
        break;
    case $method === 'GET' && $path === '/books/create':
        $bookController->create();
        break;
    case $method === 'POST' && $path === '/books/create':
        $bookController->store($_POST);
        break;
    case $method === 'GET' && $path === '/loans':
        $loanController->index();
        break;
    case $method === 'GET' && $path === '/loans/create':
        $loanController->create();
        break;
    case $method === 'POST' && $path === '/loans/create':
        $loanController->store($_POST);
        break;
    case $method === 'POST' && preg_match('#^/loans/(\d+)/return$#', $path, $matches) === 1:
        $loanController->return((int) $matches[1]);
        break;
    default:
        http_response_code(404);
        echo 'Not found';
}

