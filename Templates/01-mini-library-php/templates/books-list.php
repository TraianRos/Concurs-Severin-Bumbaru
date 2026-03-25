<section class="section-header">
    <p>Available books in the local catalog.</p>
    <a class="button-link" href="/books/create">Add new book</a>
</section>

<div class="table-shell">
    <table>
        <thead>
            <tr>
                <th>Title</th>
                <th>Author</th>
                <th>Category</th>
                <th>Copies</th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($books as $book): ?>
                <tr>
                    <td><?= htmlspecialchars($book->title, ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= htmlspecialchars($book->author, ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= htmlspecialchars($book->category, ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= $book->availableCopies ?></td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
</div>

