<section class="section-header">
    <p>Track who borrowed each book and when it should return.</p>
    <a class="button-link" href="/loans/create">Create loan</a>
</section>

<div class="table-shell">
    <table>
        <thead>
            <tr>
                <th>Book</th>
                <th>Member</th>
                <th>Loan date</th>
                <th>Return date</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($loans as $loan): ?>
                <tr>
                    <td><?= htmlspecialchars($loan->bookTitle, ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= htmlspecialchars($loan->memberName, ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= htmlspecialchars($loan->loanDate, ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= htmlspecialchars((string) $loan->returnDate, ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= htmlspecialchars($loan->status, ENT_QUOTES, 'UTF-8') ?></td>
                    <td>
                        <?php if ($loan->status === 'borrowed'): ?>
                            <form method="post" action="/loans/<?= $loan->id ?>/return">
                                <button type="submit">Mark return</button>
                            </form>
                        <?php else: ?>
                            <span class="muted-text">Completed</span>
                        <?php endif; ?>
                    </td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
</div>

