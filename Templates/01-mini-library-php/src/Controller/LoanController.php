<?php

declare(strict_types=1);

namespace App\Controller;

use App\Repository\BookRepository;
use App\Repository\LoanRepository;
use App\Repository\MemberRepository;
use App\Service\LibraryService;

final class LoanController extends BaseController
{
    public function __construct(
        private readonly LoanRepository $loanRepository,
        private readonly BookRepository $bookRepository,
        private readonly MemberRepository $memberRepository,
        private readonly LibraryService $libraryService
    ) {
    }

    public function index(): void
    {
        $this->render('loans-list', [
            'pageTitle' => 'Loans',
            'loans' => $this->loanRepository->all(),
        ]);
    }

    public function create(): void
    {
        $this->render('loans-form', [
            'pageTitle' => 'Create Loan',
            'books' => $this->bookRepository->all(),
            'members' => $this->memberRepository->all(),
        ]);
    }

    public function store(array $input): void
    {
        $result = $this->libraryService->createLoan($input);
        $target = $result['ok'] ? '/loans' : '/loans/create';
        $this->redirect($target, $result['message']);
    }

    public function return(int $loanId): void
    {
        $result = $this->libraryService->returnLoan($loanId);
        $this->redirect('/loans', $result['message']);
    }
}

