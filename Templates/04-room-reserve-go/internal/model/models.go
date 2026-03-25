package model

type Room struct {
	ID       int
	Name     string
	Capacity int
	Location string
}

type TimeSlot struct {
	ID        int
	StartTime string
	EndTime   string
}

type Reservation struct {
	RoomID           int
	ReservedBy       string
	SlotID           int
	ReservationDate  string
	Purpose          string
}

type ReservationView struct {
	ID              int
	RoomName        string
	ReservedBy      string
	StartTime       string
	EndTime         string
	ReservationDate string
	Purpose         string
}

