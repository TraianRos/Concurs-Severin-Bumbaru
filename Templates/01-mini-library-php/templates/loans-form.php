<section class="form-shell">
    <p>Select a book, a member and the loan date.</p>

    <form method="post" action="/loans/create">
        <label>
            <span>Book</span>
            <select name="book_id" required>
                <option value="">Select a book</option>
                <?php foreach ($books as $book): ?>
                    <option value="<?= $book->id ?>">
                        <?= htmlspecialchars($book->title . ' (' . $book->availableCopies . ' copies)', ENT_QUOTES, 'UTF-8') ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </label>

        <label>
            <span>Member</span>
            <select name="member_id" required>
                <option value="">Select a member</option>
                <?php foreach ($members as $member): ?>
                    <option value="<?= $member->id ?>">
                        <?= htmlspecialchars($member->fullName, ENT_QUOTES, 'UTF-8') ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </label>

        <label>
            <span>Loan date</span>
            <input type="date" name="loan_date" required>
        </label>

        <button type="submit">Create loan</button>
    </form>
</section>

