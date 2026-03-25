package service

import (
	"context"
	"errors"
	"strings"

	"roomreserve/internal/model"
	"roomreserve/internal/repository"
)

type ReservationService struct {
	store repository.Store
}

func NewReservationService(store repository.Store) *ReservationService {
	return &ReservationService{store: store}
}

func (service *ReservationService) ListRooms(ctx context.Context) ([]model.Room, error) {
	return service.store.ListRooms(ctx)
}

func (service *ReservationService) ListReservations(ctx context.Context) ([]model.ReservationView, error) {
	return service.store.ListReservations(ctx)
}

func (service *ReservationService) AvailableSlots(ctx context.Context, roomID int, date string) ([]model.TimeSlot, error) {
	timeSlots, err := service.store.ListTimeSlots(ctx)
	if err != nil {
		return nil, err
	}

	reserved, err := service.store.ReservedSlotIDs(ctx, roomID, date)
	if err != nil {
		return nil, err
	}

	var available []model.TimeSlot
	for _, slot := range timeSlots {
		if !reserved[slot.ID] {
			available = append(available, slot)
		}
	}

	return available, nil
}

func (service *ReservationService) CreateReservation(ctx context.Context, reservation model.Reservation) error {
	reservation.ReservedBy = strings.TrimSpace(reservation.ReservedBy)
	reservation.Purpose = strings.TrimSpace(reservation.Purpose)
	reservation.ReservationDate = strings.TrimSpace(reservation.ReservationDate)

	if reservation.RoomID < 1 || reservation.SlotID < 1 {
		return errors.New("room and time slot are required")
	}

	if reservation.ReservedBy == "" || reservation.Purpose == "" || reservation.ReservationDate == "" {
		return errors.New("reserved by, purpose and date are required")
	}

	reservedSlots, err := service.store.ReservedSlotIDs(ctx, reservation.RoomID, reservation.ReservationDate)
	if err != nil {
		return err
	}

	if reservedSlots[reservation.SlotID] {
		return errors.New("the selected slot is already reserved")
	}

	return service.store.CreateReservation(ctx, reservation)
}

