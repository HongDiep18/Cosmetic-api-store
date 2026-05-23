# Cosmetic Store API

A RESTful API for a cosmetic e-commerce platform built with **FastAPI**, **MongoDB**, and **Beanie ODM**.

---

## Tech Stack:

### Backend

| Library                                                                           | Version | Purpose                                    |
| --------------------------------------------------------------------------------- | ------- | ------------------------------------------ |
| [Python](https://www.python.org/)                                                 | 3.12    | Runtime language                           |
| [FastAPI](https://fastapi.tiangolo.com/)                                          | 0.115.0 | Web framework (async, auto-generated docs) |
| [Uvicorn](https://www.uvicorn.org/)                                               | 0.30.6  | ASGI server                                |
| [Pydantic](https://docs.pydantic.dev/)                                            | 2.9.2   | Data validation and serialization          |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | 2.6.0   | Settings management via `.env`             |
| [python-multipart](https://github.com/Kludex/python-multipart)                    | 0.0.9   | File upload support (product images)       |
| [email-validator](https://github.com/JoshData/python-email-validator)             | 2.2.0   | Email format validation                    |

### Database

| Library                                    | Version | Purpose                                        |
| ------------------------------------------ | ------- | ---------------------------------------------- |
| [MongoDB](https://www.mongodb.com/)        | 7.0     | NoSQL document database                        |
| [Beanie](https://beanie-odm.dev/)          | 1.26.0  | Async ODM (Object-Document Mapper) for MongoDB |
| [Motor](https://motor.readthedocs.io/)     | 3.3.2   | Async MongoDB driver (used by Beanie)          |
| [PyMongo](https://pymongo.readthedocs.io/) | 4.6.3   | Sync MongoDB driver                            |

### Security & Authentication

| Library                                               | Version | Purpose                                |
| ----------------------------------------------------- | ------- | -------------------------------------- |
| [python-jose](https://github.com/mpdavis/python-jose) | 3.3.0   | JWT token creation and verification    |
| [passlib](https://passlib.readthedocs.io/)            | 1.7.4   | Password hashing framework             |
| [bcrypt](https://github.com/pyca/bcrypt/)             | 4.0.1   | Bcrypt hashing algorithm for passwords |

### Infrastructure

| Tool                                               | Version | Purpose                                       |
| -------------------------------------------------- | ------- | --------------------------------------------- |
| [Docker](https://www.docker.com/)                  | Latest  | Container runtime                             |
| [Docker Compose](https://docs.docker.com/compose/) | Latest  | Multi-container orchestration (API + MongoDB) |

---

## Prerequisites

| Tool           | Version | Download                                               |
| -------------- | ------- | ------------------------------------------------------ |
| Docker Desktop | Latest  | https://www.docker.com/products/docker-desktop         |
| Python         | 3.12+   | https://www.python.org/downloads/ (only for local run) |

---

## Option 1 — Run with Docker (Recommended)

This is the easiest way. Docker will start both the API and MongoDB automatically.

### 1. Clone the repository

```bash
git clone https://github.com/HongDiep18/Cosmetic-api-store.git
cd Cosmetic-api-store
```

### 2. Create the `.env` file

Copy the example below and save it as `.env` in the project root

### 3. Start the services

```bash
docker compose up -d --build
```

- `-d` runs containers in the background
- `--build` rebuilds the image when code changes

### 4. Verify it is running

```bash
docker compose ps
```

Both `cosmetic_api` and `mongodb` containers should show **Up**.

### 5. Open the API docs

| URL                         | Description                       |
| --------------------------- | --------------------------------- |
| http://localhost:8000       | Health check (`{"status": "ok"}`) |
| http://localhost:8000/docs  | Swagger UI (interactive)          |
| http://localhost:8000/redoc | ReDoc (read-only)                 |

### 6. Stop the services

```bash
docker compose down
```

To also delete the MongoDB data volume:

```bash
docker compose down -v
```

---

## Option 2 — Run Locally (Without Docker)

Use this if you want to develop without Docker. You still need MongoDB running locally or a connection URI.

### 1. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure `.env` for local MongoDB

Edit `.env` and change the `MONGODB_URI` to point to your local MongoDB instance

### 4. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag restarts the server automatically when you save a file.

### 5. Open the API docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Project Structure

```
Cosmetic-api-store/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py        # Settings (loaded from .env)
│   │   ├── security.py      # JWT helpers
│   │   └── deps.py          # Dependency injection
│   ├── db/
│   │   └── init.py          # MongoDB / Beanie init
│   └── modules/             # Feature modules
│       ├── auth/            # Login, register, JWT
│       ├── users/           # User management
│       ├── products/        # Product CRUD + image upload
│       ├── categories/      # Product categories
│       ├── brands/          # Brands
│       ├── orders/          # Order management
│       ├── reviews/         # Product reviews
│       ├── shippers/        # Shipper portal
│       ├── shipments/       # Shipment tracking
│       ├── payments/        # Payment records
│       └── account/         # Account settings
├── public/uploads/          # Uploaded product images
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

## API Overview

| Prefix            | Module                           |
| ----------------- | -------------------------------- |
| `/api/auth`       | Authentication (login, register) |
| `/api/users`      | User management                  |
| `/api/products`   | Products + image upload          |
| `/api/categories` | Categories                       |
| `/api/brands`     | Brands                           |
| `/api/orders`     | Orders                           |
| `/api/reviews`    | Reviews                          |
| `/api/shippers`   | Shipper portal                   |
| `/api/shipments`  | Shipments                        |
| `/api/payments`   | Payments                         |
| `/api/accounts`   | Account settings                 |

Full interactive docs are at `/docs` after starting the server.

---

## Uploaded Images

Product images are stored in `public/uploads/` and served at:

```
http://localhost:8000/uploads/<filename>
```

In Docker, this folder is mounted as a volume so files persist across container restarts.

---

## Common Commands

```bash
# View live logs
docker compose logs -f api

# Rebuild after code changes
docker compose up -d --build

# Open a shell inside the API container
docker exec -it cosmetic_api bash

# Connect to MongoDB shell
docker exec -it mongodb mongosh
```

---

## Seed Sample Data

The project includes `seed.py` which inserts sample data into every collection so you can test the API immediately after cloning.

### What it seeds

| Collection | Rows |
| ---------- | ---- |
| roles      | 3    |
| accounts   | 5    |
| users      | 3    |
| shippers   | 3    |
| categories | 4    |
| brands     | 3    |
| products   | 15   |
| orders     | 3    |
| payments   | 3    |
| shipments  | 3    |
| reviews    | 3    |

### Run the seed (Docker — recommended)

> **Important:** If you added `seed.py` after the containers were already built, you must rebuild the image first so the file is included:

```bash
# Step 1 — rebuild the image (includes seed.py)
docker compose up -d --build

# Step 2 — run the seed
docker exec -it cosmetic_api python seed.py
```

### Run the seed (local)

```bash
# Activate venv first, then:
python seed.py

# If you dont install python, you can run docker:
docker exec -it cosmetic_api python seed.py
```

> **Warning:** The seed script clears all existing data before inserting. Do not run it on a database with real data.

### Login credentials after seeding

| Email                 | Password    | Role    |
| --------------------- | ----------- | ------- |
| admin@cosmetic.com    | Admin123!   | Admin   |
| user1@cosmetic.com    | User123!    | User    |
| user2@cosmetic.com    | User123!    | User    |
| shipper1@cosmetic.com | Shipper123! | Shipper |
| shipper2@cosmetic.com | Shipper123! | Shipper |

---

## Default Roles

On first startup the API creates three roles automatically:

- `User` — regular customer
- `Admin` — store administrator
- `Shipper` — delivery personnel
