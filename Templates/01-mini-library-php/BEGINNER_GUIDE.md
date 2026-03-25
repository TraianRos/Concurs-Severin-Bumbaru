# Beginner Guide

## Ce este acest proiect

Acest proiect este o mica biblioteca digitala. Poti vedea carti, poti adauga carti si poti crea imprumuturi pentru membri.

Este un exemplu bun pentru inceput deoarece:

- totul ruleaza in acelasi loc
- nu ai frontend separat si backend separat
- vezi usor legatura dintre pagina, logica si baza de date

## Ce trebuie sa ai instalat

- PHP 8.2 sau mai nou
- MySQL sau MariaDB
- un browser

## Cum verifici daca sunt instalate

```bash
php -v
mysql --version
```

Daca aceste comenzi afiseaza versiuni, poti merge mai departe.

## Ce face fiecare tehnologie

- PHP = limbajul principal al aplicatiei
- MySQL/MariaDB = locul unde se salveaza datele
- PDO = modulul prin care PHP comunica in siguranta cu baza de date
- HTML = structura paginii
- CSS = aspectul paginii

## Setup pas cu pas

### 1. Creeaza baza de date

```bash
mysql -u root -p
```

In consola MySQL:

```sql
CREATE DATABASE mini_library CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 2. Creeaza tabelele

```bash
mysql -u root -p mini_library < sql/schema.sql
```

### 3. Adauga date de test

```bash
mysql -u root -p mini_library < sql/seed.sql
```

### 4. Configureaza conexiunea

```bash
cp .env.example .env
```

Deschide fisierul `.env` si completeaza:

- numele bazei de date
- utilizatorul
- parola

### 5. Porneste aplicatia

```bash
php -S localhost:8000 -t public
```

### 6. Deschide in browser

Acceseaza:

```text
http://localhost:8000
```

## Exista pas de compilare?

Nu. PHP nu are aici un pas separat de compilare. Scrii fisierele PHP si le rulezi direct prin serverul local.

## Ce fisiere sa citesti primele

1. `public/index.php`
2. `src/Service/LibraryService.php`
3. `src/Repository/BookRepository.php`
4. `templates/`
5. `sql/schema.sql`

## Cum functioneaza pe scurt

1. Browser-ul cere o pagina.
2. `index.php` vede ce pagina s-a cerut.
3. Controller-ul potrivit este apelat.
4. Controller-ul cere ajutorul service-ului.
5. Service-ul verifica daca operatia are sens.
6. Repository-ul vorbeste cu baza de date.
7. Rezultatul este afisat in browser.

## Ce poti arata la prezentare

- lista de carti
- adaugare carte noua
- creare imprumut
- marcare retur
- schema simpla a bazei de date

## Ce sa retii

Acesta este cel mai usor proiect din repo pentru a intelege legatura dintre:

- pagina
- codul care proceseaza cererea
- baza de date

