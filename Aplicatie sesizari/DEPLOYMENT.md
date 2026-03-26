# Deployment

Acesti pasi sunt ganditi pentru un Raspberry Pi 5 cu 8GB RAM si acces prin VPN.

## Varianta simpla pentru prima etapa

Aceasta varianta este suficienta pentru demo intern sau testare in echipa.

### 1. Instaleaza pachetele de baza

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 1.1. Pachetele Python care vor fi instalate din proiect

Acestea vin din `requirements.txt`:

- `Flask`
- `Flask-Login`
- `Flask-SQLAlchemy`
- `pytest`
- `waitress`

### 2. Copiaza proiectul pe Raspberry Pi

Exemplu de locatie:

```text
/opt/aplicatie-sesizari
```

### 3. Creeaza mediul virtual si instaleaza dependintele

```bash
cd /opt/aplicatie-sesizari
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Important:

- nu copia `.venv` de pe PC pe Raspberry Pi
- recreeaza-l pe Raspberry Pi din `requirements.txt`
- asa eviti diferente de arhitectura, de exemplu `x86_64` versus `arm64`

### 4. Configureaza variabilele de mediu

Porneste de la `.env.example`.

```bash
cp .env.example .env
```

Minim important:

- `SECRET_KEY`
- `DATABASE_URL`
- `APP_HOST=10.144.0.1`
- `APP_PORT=5000`

### 5. Initializare baza de date

```bash
source .venv/bin/activate
python seed.py
```

### 6. Rulare pentru test

```bash
source .venv/bin/activate
python run.py
```

Aplicatia va raspunde la:

```text
http://10.144.0.1:5000
```

## Varianta recomandata pentru rulare mai stabila

Pentru ceva mai curat decat `python run.py`, foloseste `waitress`.

### Comanda de pornire

```bash
cd /opt/aplicatie-sesizari
source .venv/bin/activate
waitress-serve --host 10.144.0.1 --port 5000 --call app:create_app
```

## Pornire automata cu systemd

### 1. Fisierele pregatite in proiect

- `deploy/aplicatie-sesizari.service`
- `.env.example`

Serviciul din proiect este pregatit pentru aceasta masina:

- utilizator `musca`
- proiect in `/home/musca/Documents/Aplicatie sesizari`
- bind pe `10.144.0.1:5000`

### 2. Creeaza fisierul `.env`

```bash
cd "/home/musca/Documents/Aplicatie sesizari"
cp .env.example .env
```

Editeaza `.env` si seteaza macar:

- `SECRET_KEY`
- `DATABASE_URL`

### 3. Instaleaza serviciul

```bash
sudo cp "/home/musca/Documents/Aplicatie_sesizari/deploy/aplicatie-sesizari.service" /etc/systemd/system/aplicatie-sesizari.service
sudo systemctl daemon-reload
sudo systemctl enable aplicatie-sesizari
sudo systemctl start aplicatie-sesizari
```

### 4. Verifica serviciul

```bash
sudo systemctl status aplicatie-sesizari
sudo systemctl is-active aplicatie-sesizari
curl -I http://10.144.0.1:5000
```

### 5. Vezi logurile

```bash
journalctl -u aplicatie-sesizari -n 50 --no-pager
```

## Quick Tunnel automat cu pagina locala de status

Aceasta varianta porneste automat `cloudflared`, detecteaza URL-ul public `*.trycloudflare.com`, il salveaza in fisier si afiseaza o pagina simpla de status pe un port separat din reteaua locala.

### Fisiere pregatite in proiect

- `deploy/cloudflared-quick-tunnel.service`
- `app/cloudflared_status.py`

### Variabile noi in `.env`

```env
CLOUDFLARED_BIN=/usr/bin/cloudflared
CLOUDFLARED_TARGET_URL=http://127.0.0.1:5000
CLOUDFLARED_STATUS_HOST=0.0.0.0
CLOUDFLARED_STATUS_PORT=8081
CLOUDFLARED_STATUS_FILE=instance/cloudflared_quick_tunnel.json
```

### Instalare serviciu

```bash
sudo cp "/home/musca/Documents/Aplicatie_sesizari/deploy/cloudflared-quick-tunnel.service" /etc/systemd/system/cloudflared-quick-tunnel.service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared-quick-tunnel
sudo systemctl start cloudflared-quick-tunnel
```

### Verificare

```bash
sudo systemctl status cloudflared-quick-tunnel --no-pager
journalctl -u cloudflared-quick-tunnel -n 50 --no-pager
curl http://127.0.0.1:8081/status.json
```

Pagina HTML de status va fi disponibila la:

```text
http://<IP-ul-local-al-serverului>:8081
```

JSON-ul cu ultima stare detectata va fi salvat implicit in:

```text
instance/cloudflared_quick_tunnel.json
```

## Backup minim

Pentru aceasta versiune, baza de date este fisierul:

```text
instance/aplicatie_sesizari.db
```

Un backup simplu inseamna sa copiezi periodic acest fisier.

## De ce pastram `venv` si pe server

Chiar daca Raspberry Pi-ul este dedicat proiectului, `venv` ramane util pentru:

- izolare fata de pachetele sistemului
- upgrade controlat al dependintelor
- refacere rapida daca mediul se corupe
- reproducere usoara pe alta placa sau pe alta masina

Cel mai bine este sa privesti serverul asa:

- sistemul de operare ofera `python3`, `venv` si `pip`
- proiectul isi tine singur librariile lui in `.venv`

## Observatii de retea

- daca intrati prin VPN, IP-ul mentionat de voi `10.144.0.1` este suficient pentru prima faza
- daca puneti aplicatia direct pe internet mai tarziu, trebuie adaugate reverse proxy, HTTPS si politici de securitate mai stricte
