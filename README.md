# Library Service API

---

## Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [API Endpoints](#api-endpoints)
5. [Run with Docker](#run-with-docker)
6. [Run Locally](#run-locally)
7. [Testing](#testing)
8. [Technologies](#technologies)

---

## Project Overview

Library Service API is a Django REST Framework backend for managing books, users, borrowings, payments, and notifications for a city library. It exposes public read access for books, admin-only management operations for inventory, and authenticated flows for borrowing and payment handling.

The project includes:

- JWT authentication with an email-based custom user model
- Book inventory management with CRUD endpoints
- Borrowing creation, return, filtering, and ownership rules
- Stripe checkout session creation for borrowings and fines
- Telegram notifications for new borrowings, successful payments, and overdue checks
- Celery and Redis support for background and scheduled tasks
- Swagger UI and OpenAPI schema generation

---

## Features

- Public book list and detail endpoints
- Admin-only create, update, and delete operations for books
- User registration, login, token refresh, and profile management
- User-specific borrowing list, with admin filtering by `user_id`
- Borrowing return flow with inventory restoration
- Automatic fine creation for overdue returns
- Payment list and detail endpoints with owner/admin visibility rules
- Daily overdue borrowing notifications
- Mock Stripe session fallback when Stripe credentials are not configured

---

## Project Structure

```text
library-service/
|-- config/                         # Django project configuration
|   |-- settings.py                 # Django, DRF, JWT, Celery, Stripe, and env settings
|   |-- urls.py                     # Root routes, docs, and app includes
|   |-- celery.py                   # Celery app configuration
|   |-- telegram.py                 # Telegram message sender
|   |-- asgi.py
|   |-- wsgi.py
|   `-- __init__.py
|-- users/                          # Users app
|   |-- migrations/
|   |-- admin.py
|   |-- models.py                   # Custom email-based user model
|   |-- serializers.py
|   |-- tests.py
|   |-- urls.py
|   |-- views.py
|   `-- __init__.py
|-- books/                          # Books app
|   |-- migrations/
|   |-- admin.py
|   |-- models.py                   # Book model and cover choices
|   |-- permissions.py              # Admin-or-read-only permission
|   |-- serializers.py
|   |-- tests.py
|   |-- urls.py
|   |-- views.py
|   `-- __init__.py
|-- borrowings/                     # Borrowings app
|   |-- migrations/
|   |-- admin.py
|   |-- models.py                   # Borrowing model and constraints
|   |-- serializers.py
|   |-- services.py                 # Borrowing return flow
|   |-- tasks.py                    # Telegram and overdue tasks
|   |-- tests.py
|   |-- urls.py
|   |-- views.py
|   `-- __init__.py
|-- payments/                       # Payments app
|   |-- migrations/
|   |-- admin.py
|   |-- models.py                   # Payment model
|   |-- serializers.py
|   |-- services.py                 # Stripe session and payment status logic
|   |-- tests.py
|   |-- urls.py
|   |-- views.py
|   `-- __init__.py
|-- Dockerfile
|-- docker-compose.yml
|-- .env.sample
|-- manage.py
|-- requirements.txt
`-- README.md
```

---

## API Endpoints

Base URL: `http://127.0.0.1:8000/`

Main routes:

- `/api/users/`
- `/api/users/token/`
- `/api/users/token/refresh/`
- `/api/users/me/`
- `/api/books/`
- `/api/borrowings/`
- `/api/borrowings/<id>/`
- `/api/borrowings/<id>/return/`
- `/api/payments/`
- `/api/payments/<id>/`
- `/api/payments/success/`
- `/api/payments/cancel/`

Documentation routes:

- `/api/doc/swagger/`
- `/api/schema/`
- `/admin/`

Example token request:

```http
POST /api/users/token/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

Use the access token in authenticated requests:

```text
Authorize: Bearer <access_token>
```

---

## Run with Docker

### Prerequisites

- Docker
- Docker Compose

### Start the app

1. Clone the repository and move into the project directory:

```bash
git clone https://github.com/<your-username>/library-service.git
cd library-service
```

2. Create your environment file:

```bash
cp .env.sample .env
```

Windows PowerShell:

```powershell
Copy-Item .env.sample .env
```

3. Build and start the services:

```bash
docker compose up --build
```

This starts:

- Django API on port `8000`
- PostgreSQL
- Redis
- Celery worker
- Celery beat scheduler

Open:

- `http://127.0.0.1:8000/api/doc/swagger/`
- `http://127.0.0.1:8000/api/schema/`
- `http://127.0.0.1:8000/admin/`

### Optional Docker commands

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Run tests:

```bash
docker compose exec web python manage.py test
```

Stop the app:

```bash
docker compose down
```

---

## Run Locally

### Prerequisites

- Python 3.12+
- `venv`

### Setup

1. Clone the repository and move into the project directory:

```bash
git clone https://github.com/<your-username>/library-service.git
cd library-service
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create an environment file:

```bash
cp .env.sample .env
```

Windows PowerShell:

```powershell
Copy-Item .env.sample .env
```

5. Apply migrations:

```bash
python manage.py migrate
```

6. Optionally create a superuser:

```bash
python manage.py createsuperuser
```

7. Start the development server:

```bash
python manage.py runserver
```

8. Optionally run background services:

```bash
celery -A config worker -l info
celery -A config beat -l info
```

---

## Testing

Run the test suite locally:

```bash
python manage.py test
```

---

## Technologies

- Python 3.12
- Django 6
- Django REST Framework
- Simple JWT
- drf-spectacular
- Celery
- Redis
- Stripe Python SDK
- PostgreSQL
- SQLite
- Docker and Docker Compose

---

Developed by [mishagitcode](https://github.com/mishagitcode)
