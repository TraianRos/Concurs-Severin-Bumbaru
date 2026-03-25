package handler

import (
	"context"
	"encoding/json"
	"html/template"
	"net/http"
	"strconv"
	"time"

	"roomreserve/internal/model"
	"roomreserve/internal/service"
)

type Handler struct {
	service   *service.ReservationService
	templates *template.Template
}

type viewData struct {
	PageTitle    string
	Message      string
	Rooms        []model.Room
	Reservations []model.ReservationView
	Slots        []model.TimeSlot
}

func New(service *service.ReservationService, templates *template.Template) *Handler {
	return &Handler{service: service, templates: templates}
}

func (handler *Handler) Home(response http.ResponseWriter, request *http.Request) {
	ctx, cancel := context.WithTimeout(request.Context(), 3*time.Second)
	defer cancel()

	rooms, _ := handler.service.ListRooms(ctx)
	reservations, _ := handler.service.ListReservations(ctx)

	handler.render(response, "home.html", viewData{
		PageTitle:    "Dashboard",
		Rooms:        rooms,
		Reservations: reservations,
	})
}

func (handler *Handler) Rooms(response http.ResponseWriter, request *http.Request) {
	ctx, cancel := context.WithTimeout(request.Context(), 3*time.Second)
	defer cancel()

	rooms, _ := handler.service.ListRooms(ctx)
	handler.render(response, "rooms.html", viewData{
		PageTitle: "Rooms",
		Rooms:     rooms,
	})
}

func (handler *Handler) NewReservation(response http.ResponseWriter, request *http.Request) {
	ctx, cancel := context.WithTimeout(request.Context(), 3*time.Second)
	defer cancel()

	rooms, _ := handler.service.ListRooms(ctx)
	slots, _ := handler.service.AvailableSlots(ctx, 1, time.Now().Format("2006-01-02"))

	handler.render(response, "reservation_form.html", viewData{
		PageTitle: "New reservation",
		Rooms:     rooms,
		Slots:     slots,
	})
}

func (handler *Handler) CreateReservation(response http.ResponseWriter, request *http.Request) {
	if err := request.ParseForm(); err != nil {
		http.Error(response, "invalid form data", http.StatusBadRequest)
		return
	}

	roomID, _ := strconv.Atoi(request.FormValue("room_id"))
	slotID, _ := strconv.Atoi(request.FormValue("slot_id"))

	reservation := model.Reservation{
		RoomID:          roomID,
		ReservedBy:      request.FormValue("reserved_by"),
		SlotID:          slotID,
		ReservationDate: request.FormValue("reservation_date"),
		Purpose:         request.FormValue("purpose"),
	}

	ctx, cancel := context.WithTimeout(request.Context(), 3*time.Second)
	defer cancel()

	if err := handler.service.CreateReservation(ctx, reservation); err != nil {
		rooms, _ := handler.service.ListRooms(ctx)
		slots, _ := handler.service.AvailableSlots(ctx, roomID, reservation.ReservationDate)
		response.WriteHeader(http.StatusBadRequest)
		handler.render(response, "reservation_form.html", viewData{
			PageTitle: "New reservation",
			Message:   err.Error(),
			Rooms:     rooms,
			Slots:     slots,
		})
		return
	}

	http.Redirect(response, request, "/", http.StatusSeeOther)
}

func (handler *Handler) AvailableSlots(response http.ResponseWriter, request *http.Request) {
	roomID, _ := strconv.Atoi(request.URL.Query().Get("room_id"))
	date := request.URL.Query().Get("date")

	if roomID < 1 || date == "" {
		http.Error(response, "room_id and date are required", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(request.Context(), 3*time.Second)
	defer cancel()

	slots, err := handler.service.AvailableSlots(ctx, roomID, date)
	if err != nil {
		http.Error(response, "could not load slots", http.StatusInternalServerError)
		return
	}

	response.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(response).Encode(slots)
}

func (handler *Handler) Health(response http.ResponseWriter, request *http.Request) {
	response.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(response).Encode(map[string]string{"status": "ok", "app": "room-reserve"})
}

func (handler *Handler) render(response http.ResponseWriter, name string, data viewData) {
	if err := handler.templates.ExecuteTemplate(response, "base.html", map[string]any{
		"PageTitle":    data.PageTitle,
		"Message":      data.Message,
		"Rooms":        data.Rooms,
		"Reservations": data.Reservations,
		"Slots":        data.Slots,
		"Content":      name,
	}); err != nil {
		http.Error(response, "template rendering failed", http.StatusInternalServerError)
	}
}

