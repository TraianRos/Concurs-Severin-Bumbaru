<section class="stats-grid">
    <article class="stat-block">
        <span>Total books</span>
        <strong><?= (int) $stats['bookCount'] ?></strong>
    </article>
    <article class="stat-block">
        <span>Total members</span>
        <strong><?= (int) $stats['memberCount'] ?></strong>
    </article>
    <article class="stat-block">
        <span>Active loans</span>
        <strong><?= (int) $stats['activeLoans'] ?></strong>
    </article>
</section>

<section class="action-row">
    <a class="button-link" href="/books/create">Add book</a>
    <a class="button-link button-link--secondary" href="/loans/create">Create loan</a>
</section>

