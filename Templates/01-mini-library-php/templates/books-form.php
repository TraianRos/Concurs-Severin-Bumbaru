<section class="form-shell">
    <p>Use this form to add a new book to the catalog.</p>

    <form method="post" action="/books/create">
        <label>
            <span>Title</span>
            <input type="text" name="title" required>
        </label>

        <label>
            <span>Author</span>
            <input type="text" name="author" required>
        </label>

        <label>
            <span>Category</span>
            <input type="text" name="category" required>
        </label>

        <label>
            <span>Available copies</span>
            <input type="number" min="1" name="available_copies" required>
        </label>

        <button type="submit">Save book</button>
    </form>
</section>

