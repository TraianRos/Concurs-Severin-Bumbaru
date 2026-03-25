INSERT INTO rooms (name, capacity, location) VALUES
('Aula Nord', 50, 'Building A'),
('Lab OOP', 24, 'Building B'),
('Conference Room', 12, 'Building C');

INSERT INTO time_slots (start_time, end_time) VALUES
('09:00', '10:00'),
('10:00', '11:00'),
('11:00', '12:00'),
('13:00', '14:00'),
('14:00', '15:00');

INSERT INTO reservations (room_id, reserved_by, slot_id, reservation_date, purpose) VALUES
(2, 'Ana Ionescu', 2, '2026-04-08', 'Practice presentation');

