package main

import (
	"database/sql"
	"html/template"
	"log"
	"net/http"
	"time"

	_ "modernc.org/sqlite"

	"roomreserve/internal/config"
	"roomreserve/internal/handler"
	"roomreserve/internal/repository"
	"roomreserve/internal/service"
)

func main() {
	cfg := config.Load()

	db, err := sql.Open("sqlite", cfg.DBPath)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	templates := template.Must(template.ParseGlob("web/templates/*.html"))

	reservationRepository := repository.NewSQLiteRepository(db)
	reservationService := service.NewReservationService(reservationRepository)
	roomHandler := handler.New(reservationService, templates)

	mux := http.NewServeMux()
	mux.HandleFunc("/", roomHandler.Home)
	mux.HandleFunc("/rooms", roomHandler.Rooms)
	mux.HandleFunc("/reservations/new", func(response http.ResponseWriter, request *http.Request) {
		if request.Method == http.MethodPost {
			roomHandler.CreateReservation(response, request)
			return
		}

		roomHandler.NewReservation(response, request)
	})
	mux.HandleFunc("/api/slots", roomHandler.AvailableSlots)
	mux.HandleFunc("/health", roomHandler.Health)
	mux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir("web/static"))))

	server := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           mux,
		ReadHeaderTimeout: 3 * time.Second,
		ReadTimeout:       5 * time.Second,
		WriteTimeout:      10 * time.Second,
		IdleTimeout:       30 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}

	log.Printf("RoomReserve listening on http://localhost:%s", cfg.Port)
	log.Fatal(server.ListenAndServe())
}

