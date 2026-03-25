# Setup Checklist

Acest workspace este gandit pentru rulare nativa pe host. Mediul curent nu are toate runtime-urile instalate, deci foloseste lista de mai jos inainte de demo.

## Runtime-uri

- PHP 8.2+ cu extensia PDO si driver MySQL
- Node.js 20 LTS si npm
- Python 3.12+ si `venv`
- Go 1.22+
- Emscripten pentru compilarea modulului WebAssembly

## Baze de date

- MySQL sau MariaDB pentru proiectul PHP
- PostgreSQL pentru proiectul React + Express
- SQLite pentru Flask, Go si FastAPI

## Verificari rapide

- `php -v`
- `node -v`
- `npm -v`
- `python3 --version`
- `go version`
- `emcc --version`

## Observatie

Daca lipseste `emcc`, proiectul `05-quiz-lab-fastapi-wasm` poate fi explicat si demonstrat cu artefactele precompilate din repo, dar sursa C++ ramane punctul de referinta.

