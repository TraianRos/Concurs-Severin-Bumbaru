<?php

declare(strict_types=1);

namespace App\Service;

use App\Repository\BookRepository;
use App\Repository\LoanRepository;
use App\Repository\MemberRepository;

final class LibraryService
{
    public function __construct(
        private readonly BookRepository $bookRepository,
        private readonly MemberRepository $memberRepository,
        private readonly LoanRepository $loanRepository
    ) {
    }

    public function dashboard(): array
    {
        return [
            'bookCount' => $this->bookRepository->count(),
            'memberCount' => $this->memberRepository->count(),
            'activeLoans' => $this->loanRepository->activeCount(),
        ];
    }

    public function addBook(array $input): array
    {
        $title = trim((string) ($input['title'] ?? ''));
        $author = trim((string) ($input['author'] ?? ''));
        $category = trim((string) ($input['category'] ?? ''));
        $copies = (int) ($input['available_copies'] ?? 0);

        if ($title === '' || $author === '' || $category === '' || $copies < 1) {
            return ['ok' => false, 'message' => 'All fields are required and copies must be positive.'];
        }

        $this->bookRepository->create($title, $author, $category, $copies);

        return ['ok' => true, 'message' => 'Book added successfully.'];
    }

    public function createLoan(array $input): array
    {
        $bookId = (int) ($input['book_id'] ?? 0);
        $memberId = (int) ($input['member_id'] ?? 0);
        $loanDate = trim((string) ($input['loan_date'] ?? ''));

        if ($bookId < 1 || $memberId < 1 || $loanDate === '') {
            return ['ok' => false, 'message' => 'Select a book, member and loan date.'];
        }

        $book = $this->bookRepository->find($bookId);
        if ($book === null) {
            return ['ok' => false, 'message' => 'The selected book does not exist.'];
        }

        if ($book->availableCopies < 1) {
            return ['ok' => false, 'message' => 'No available copies for this book.'];
        }

        $this->loanRepository->create($bookId, $memberId, $loanDate);
        $this->bookRepository->decrementCopies($bookId);

        return ['ok' => true, 'message' => 'Loan created successfully.'];
    }

    public function returnLoan(int $loanId): array
    {
        if ($loanId < 1) {
            return ['ok' => false, 'message' => 'Invalid loan id.'];
        }

        $bookId = $this->loanRepository->findBorrowedBookId($loanId);
        if ($bookId === null) {
            return ['ok' => false, 'message' => 'Loan not found or already returned.'];
        }

        $today = date('Y-m-d');
        $this->loanRepository->markReturned($loanId, $today);
        $this->bookRepository->incrementCopies($bookId);

        return ['ok' => true, 'message' => 'Loan marked as returned.'];
    }
}

