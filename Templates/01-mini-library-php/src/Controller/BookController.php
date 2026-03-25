<?php

declare(strict_types=1);

namespace App\Controller;

use App\Repository\BookRepository;
use App\Service\LibraryService;

final class BookController extends BaseController
{
    public function __construct(
        private readonly BookRepository $bookRepository,
        private readonly LibraryService $libraryService
    ) {
    }

    public function index(): void
    {
        $this->render('books-list', [
            'pageTitle' => 'Books',
            'books' => $this->bookRepository->all(),
        ]);
    }

    public function create(): void
    {
        $this->render('books-form', [
            'pageTitle' => 'Add Book',
        ]);
    }

    public function store(array $input): void
    {
        $result = $this->libraryService->addBook($input);
        $target = $result['ok'] ? '/books' : '/books/create';
        $this->redirect($target, $result['message']);
    }
}

