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

Minim important:

- `SECRET_KEY`
- `DATABASE_URL`
- `APP_HOST=0.0.0.0`
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
waitress-serve --host 0.0.0.0 --port 5000 run:app
```

## Pornire automata cu systemd

### 1. Creeaza fisierul

```bash
sudo nano /etc/systemd/system/aplicatie-sesizari.service
```

### 2. Continut exemplu

```ini
[Unit]
Description=Aplicatie sesizari
After=network.target

[Service]
User=pi
WorkingDirectory=/opt/aplicatie-sesizari
Environment=SECRET_KEY=schimba-aici-cheia
Environment=DATABASE_URL=sqlite:///aplicatie_sesizari.db
Environment=APP_HOST=0.0.0.0
Environment=APP_PORT=5000
ExecStart=/opt/aplicatie-sesizari/.venv/bin/waitress-serve --host 0.0.0.0 --port 5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Activeaza serviciul

```bash
sudo systemctl daemon-reload
sudo systemctl enable aplicatie-sesizari
sudo systemctl start aplicatie-sesizari
sudo systemctl status aplicatie-sesizari
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
