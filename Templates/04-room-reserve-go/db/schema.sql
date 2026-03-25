CREATE TABLE rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE time_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    reserved_by TEXT NOT NULL,
    slot_id INTEGER NOT NULL,
    reservation_date TEXT NOT NULL,
    purpose TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    FOREIGN KEY (slot_id) REFERENCES time_slots(id),
    UNIQUE (room_id, slot_id, reservation_date)
);

