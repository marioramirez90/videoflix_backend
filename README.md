# Videoflix Backend API

![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![Django](https://img.shields.io/badge/django-5.x-green.svg)
![DRF](https://img.shields.io/badge/DRF-SimpleJWT-red.svg)
![Docker](https://img.shields.io/badge/docker-compose-blue.svg)

Robust REST API backend for the Videoflix video streaming platform. Built with **Django**, **Django REST Framework (DRF)**, **PostgreSQL**, **Redis**, **django-rq**, and **FFmpeg**.

---

## Table of Contents

- [Quickstart (Local with Docker)](#quickstart-local-with-docker)
- [Features](#features)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Prerequisites](#prerequisites)
- [API Endpoints](#api-endpoints)
- [HLS Streaming Pipeline & Worker](#hls-streaming-pipeline--worker)
- [Email Configuration](#email-configuration)
- [Frontend Integration (CORS & Cookies)](#frontend-integration-cors--cookies)

---

## Quickstart (Local with Docker)

### 1. Clone Repository & Set Up Environment Variables

```bash
git clone <your-repo-url>
cd videoflix_backend
```

Create a `.env` file in the root directory (see template below):

```env
SECRET_KEY=your-secret-django-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=videoflix_db
POSTGRES_USER=videoflix_user
POSTGRES_PASSWORD=supersecretpassword
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email (Console for local development and automated testing)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 2. Build and Start Containers

```bash
docker compose up -d --build
```

On startup, static files are collected, migrations are automatically applied, and the RQ worker is launched.

### 3. Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

The backend is now accessible at `http://127.0.0.1:8000/`. The Django admin dashboard is available at `http://127.0.0.1:8000/admin/`.

---

## Features

- **JWT Authentication with HttpOnly Cookies:**
  - Tokens (`access_token` and `refresh_token`) are securely stored in `HttpOnly` cookies.
  - Seamless token refresh flow and automatic session invalidation via token blacklisting on logout.
- **Multi-Resolution HLS Streaming:**
  - Asynchronous video transcoding powered by Redis Queue (`django-rq`) and FFmpeg into `480p`, `720p`, and `1080p`.
  - Delivery of dynamic master playlists (`index.m3u8`) and binary video segments (`.ts`).
- **Automatic Thumbnail Extraction:**
  - FFmpeg automatically extracts a preview still from second 1 upon upload and links it as a thumbnail.
- **Account Activation & Password Reset:**
  - Email-based account activation and password reset flows (developer-friendly via console or production SMTP via Brevo).

---

## Architecture & Tech Stack

- **Backend:** Python 3.12, Django, Django REST Framework, SimpleJWT
- **Database:** PostgreSQL
- **Task Queue & Cache:** Redis, `django-rq`
- **Video Processing:** FFmpeg, Pillow
- **Containerization:** Docker Compose (Services: `web`, `db`, `redis`)

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- Git installed.

---

## API Endpoints

### Authentication (`/api/`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register/` | Registers new user, sends activation email |
| `GET` | `/api/activate/<uidb64>/<token>/` | Activates user account |
| `POST` | `/api/login/` | Validates credentials, sets HttpOnly cookies |
| `POST` | `/api/token/refresh/` | Renews access token via refresh cookie |
| `POST` | `/api/logout/` | Invalidates refresh token & clears cookies |
| `POST` | `/api/password_reset/` | Dispatches email with reset token |
| `POST` | `/api/password_confirm/<uidb64>/<token>/` | Resets password with valid token |

### Videos & HLS Streaming (`/api/video/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/video/` | List all videos with absolute thumbnail URLs |
| `GET` | `/api/video/<id>/<res>/index.m3u8` | Master playlist for 480p, 720p, or 1080p |
| `GET` | `/api/video/<id>/<res>/<segment>/` | Binary HLS transport stream segment (.ts) |

---

## HLS Streaming Pipeline & Worker

1. **Upload:** A video file (`.mp4`) is uploaded via the Django admin interface or API.
2. **Signal:** A `post_save` model signal enqueues the conversion task into the default Redis queue.
3. **Thumbnail:** FFmpeg captures a snapshot at timestamp `00:00:01` and stores it under `/media/thumbnails/`.
4. **HLS Transcoding:** FFmpeg generates playlists and `.ts` chunk files for `480p`, `720p`, and `1080p` resolutions under `/media/videos/<id>/`.

To monitor the background worker live:

```bash
docker compose logs -f web
```

---

## Email Configuration

By default, the console backend is active. Registration and password reset links are printed directly to the terminal or container logs:

```bash
docker compose logs web --tail 50
```

For sending HTML emails via SMTP (e.g., using Brevo), configure the following in your `.env` file:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_smtp_login
EMAIL_HOST_PASSWORD=your_smtp_key
DEFAULT_FROM_EMAIL=Videoflix <your-verified-email@domain.com>
```

---

## Frontend Integration (CORS & Cookies)

The backend is pre-configured for Single-Page Applications (SPA):

- **Allowed Origins:** `http://127.0.0.1:5500`, `http://localhost:5500`, `http://localhost:4200`, `http://localhost:3000`, `http://localhost:5173`
- `CORS_ALLOW_CREDENTIALS = True`
- `SESSION_COOKIE_SAMESITE = 'Lax'` / `CSRF_COOKIE_SAMESITE = 'Lax'`
- In development mode (`DEBUG = True`), secure flags are set to `False` so cookies can be transmitted over plain `http://`.
