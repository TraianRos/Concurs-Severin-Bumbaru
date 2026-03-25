package service

import (
	"context"
	"testing"

	"roomreserve/internal/model"
)

type fakeStore struct {
	reserved map[int]bool
}

func (store *fakeStore) ListRooms(ctx context.Context) ([]model.Room, error) {
	return nil, nil
}

func (store *fakeStore) ListReservations(ctx context.Context) ([]model.ReservationView, error) {
	return nil, nil
}

func (store *fakeStore) ListTimeSlots(ctx context.Context) ([]model.TimeSlot, error) {
	return []model.TimeSlot{{ID: 1}, {ID: 2}}, nil
}

func (store *fakeStore) ReservedSlotIDs(ctx context.Context, roomID int, date string) (map[int]bool, error) {
	return store.reserved, nil
}

func (store *fakeStore) CreateReservation(ctx context.Context, reservation model.Reservation) error {
	return nil
}

func TestCreateReservationRejectsOverlap(t *testing.T) {
	service := NewReservationService(&fakeStore{reserved: map[int]bool{2: true}})

	err := service.CreateReservation(context.Background(), model.Reservation{
		RoomID:          1,
		SlotID:          2,
		ReservedBy:      "Ana",
		ReservationDate: "2026-04-08",
		Purpose:         "Practice",
	})

	if err == nil {
		t.Fatal("expected overlap error")
	}
}

