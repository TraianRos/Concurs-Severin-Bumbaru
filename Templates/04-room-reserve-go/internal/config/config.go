package config

import (
	"bufio"
	"os"
	"strings"
)

type Config struct {
	Port   string
	DBPath string
}

func Load() Config {
	loadDotEnv(".env")

	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8080"
	}

	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "./room_reserve.db"
	}

	return Config{
		Port:   port,
		DBPath: dbPath,
	}
}

func loadDotEnv(path string) {
	file, err := os.Open(path)
	if err != nil {
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") || !strings.Contains(line, "=") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		if os.Getenv(key) == "" {
			_ = os.Setenv(key, value)
		}
	}
}
