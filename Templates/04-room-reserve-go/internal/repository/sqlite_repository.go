package repository

import (
	"context"
	"database/sql"

	"roomreserve/internal/model"
)

type Store interface {
	ListRooms(ctx context.Context) ([]model.Room, error)
	ListReservations(ctx context.Context) ([]model.ReservationView, error)
	ListTimeSlots(ctx context.Context) ([]model.TimeSlot, error)
	ReservedSlotIDs(ctx context.Context, roomID int, date string) (map[int]bool, error)
	CreateReservation(ctx context.Context, reservation model.Reservation) error
}

type SQLiteRepository struct {
	DB *sql.DB
}

func NewSQLiteRepository(db *sql.DB) *SQLiteRepository {
	return &SQLiteRepository{DB: db}
}

func (repository *SQLiteRepository) ListRooms(ctx context.Context) ([]model.Room, error) {
	rows, err := repository.DB.QueryContext(ctx, "SELECT id, name, capacity, location FROM rooms ORDER BY name")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var rooms []model.Room
	for rows.Next() {
		var room model.Room
		if err := rows.Scan(&room.ID, &room.Name, &room.Capacity, &room.Location); err != nil {
			return nil, err
		}
		rooms = append(rooms, room)
	}

	return rooms, rows.Err()
}

func (repository *SQLiteRepository) ListReservations(ctx context.Context) ([]model.ReservationView, error) {
	rows, err := repository.DB.QueryContext(ctx, `
		SELECT
			r.id,
			rm.name,
			r.reserved_by,
			ts.start_time,
			ts.end_time,
			r.reservation_date,
			r.purpose
		FROM reservations r
		JOIN rooms rm ON rm.id = r.room_id
		JOIN time_slots ts ON ts.id = r.slot_id
		ORDER BY r.reservation_date, ts.start_time
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var reservations []model.ReservationView
	for rows.Next() {
		var reservation model.ReservationView
		if err := rows.Scan(
			&reservation.ID,
			&reservation.RoomName,
			&reservation.ReservedBy,
			&reservation.StartTime,
			&reservation.EndTime,
			&reservation.ReservationDate,
			&reservation.Purpose,
		); err != nil {
			return nil, err
		}
		reservations = append(reservations, reservation)
	}

	return reservations, rows.Err()
}

func (repository *SQLiteRepository) ListTimeSlots(ctx context.Context) ([]model.TimeSlot, error) {
	rows, err := repository.DB.QueryContext(ctx, "SELECT id, start_time, end_time FROM time_slots ORDER BY start_time")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var timeSlots []model.TimeSlot
	for rows.Next() {
		var slot model.TimeSlot
		if err := rows.Scan(&slot.ID, &slot.StartTime, &slot.EndTime); err != nil {
			return nil, err
		}
		timeSlots = append(timeSlots, slot)
	}

	return timeSlots, rows.Err()
}

func (repository *SQLiteRepository) ReservedSlotIDs(ctx context.Context, roomID int, date string) (map[int]bool, error) {
	rows, err := repository.DB.QueryContext(
		ctx,
		"SELECT slot_id FROM reservations WHERE room_id = ? AND reservation_date = ?",
		roomID,
		date,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := map[int]bool{}
	for rows.Next() {
		var slotID int
		if err := rows.Scan(&slotID); err != nil {
			return nil, err
		}
		result[slotID] = true
	}

	return result, rows.Err()
}

func (repository *SQLiteRepository) CreateReservation(ctx context.Context, reservation model.Reservation) error {
	_, err := repository.DB.ExecContext(
		ctx,
		`
			INSERT INTO reservations (room_id, reserved_by, slot_id, reservation_date, purpose)
			VALUES (?, ?, ?, ?, ?)
		`,
		reservation.RoomID,
		reservation.ReservedBy,
		reservation.SlotID,
		reservation.ReservationDate,
		reservation.Purpose,
	)
	return err
}

