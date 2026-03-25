INSERT INTO events (title, location, start_date, seats) VALUES
('Backend Basics', 'Lab 101', '2026-04-02 10:00', 30),
('Frontend Sprint', 'Lab 204', '2026-04-03 12:00', 24);

INSERT INTO attendees (full_name, email) VALUES
('Ana Ionescu', 'ana@example.com'),
('Mihai Popescu', 'mihai@example.com');

INSERT INTO registrations (event_id, attendee_id, status) VALUES
(1, 1, 'registered');

