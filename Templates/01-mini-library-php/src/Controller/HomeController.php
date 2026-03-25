<?php

declare(strict_types=1);

namespace App\Controller;

use App\Service\LibraryService;

final class HomeController extends BaseController
{
    public function __construct(private readonly LibraryService $libraryService)
    {
    }

    public function index(): void
    {
        $this->render('dashboard', [
            'stats' => $this->libraryService->dashboard(),
            'pageTitle' => 'Dashboard',
        ]);
    }

    public function health(): void
    {
        header('Content-Type: application/json');
        echo json_encode(['status' => 'ok', 'app' => 'mini-library']);
    }
}

