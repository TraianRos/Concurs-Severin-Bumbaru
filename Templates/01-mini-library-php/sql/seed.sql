INSERT INTO books (title, author, category, available_copies) VALUES
('Clean Code', 'Robert C. Martin', 'Programming', 3),
('Design Patterns', 'Erich Gamma', 'Architecture', 2),
('The Pragmatic Programmer', 'Andrew Hunt', 'Programming', 4);

INSERT INTO members (full_name, email) VALUES
('Ana Ionescu', 'ana@example.com'),
('Mihai Popescu', 'mihai@example.com'),
('Ioana Marin', 'ioana@example.com');

INSERT INTO loans (book_id, member_id, loan_date, return_date, status) VALUES
(1, 1, '2026-03-20', NULL, 'borrowed'),
(2, 2, '2026-03-18', '2026-03-22', 'returned');

