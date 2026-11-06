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
- [Running Tests](#running-tests)

---

## Quickstart (Local with Docker)

### 1. Clone Repository & Set Up Environment Variables

```bash
git clone <your-repo-url>
cd videoflix_backend
```

Copy the environment template into a `.env` file:

```bash
cp .env.template .env
```
*(On Windows Command Prompt: `copy .env.template .env`)*

Open the `.env` file and customize your configuration values (such as `SECRET_KEY`, database credentials, superuser login, frontend URL, and SMTP email settings).

### 2. Build and Start Containers

```bash
docker compose up -d --build
```

On container startup, static files are collected, migrations are automatically applied, the background RQ worker is started, and the initial superuser is automatically created using the credentials configured in `.env` (`DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD`, default: `admin` / `adminpassword`).

The backend is now accessible at `http://127.0.0.1:8000/`.
The Django admin dashboard is available at `http://127.0.0.1:8000/admin/`.

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

For production and staging workflows, email delivery via SMTP (e.g. Brevo, SendGrid, or any standard SMTP server) should be configured so activation and password reset emails are delivered directly to real inboxes.

Set your SMTP credentials in the `.env` file (copied from `.env.template`):

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your_smtp_login
EMAIL_HOST_PASSWORD=your_smtp_password
DEFAULT_FROM_EMAIL=Videoflix <noreply@yourdomain.com>
```

> [!NOTE]
> For offline local development without external SMTP credentials, you can switch back to the console backend:
> ```env
> EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
> ```
> Registration and password reset links will then be printed directly to the container logs:
> ```bash
> docker compose logs web --tail 50
> ```

---

## Frontend Integration (CORS & Cookies)

The backend is pre-configured for Single-Page Applications (SPA):

- **Allowed Origins:** `http://127.0.0.1:5500`, `http://localhost:5500`, `http://localhost:4200`, `http://localhost:3000`, `http://localhost:5173`
- `CORS_ALLOW_CREDENTIALS = True`
- `SESSION_COOKIE_SAMESITE = 'Lax'` / `CSRF_COOKIE_SAMESITE = 'Lax'`
- In development mode (`DEBUG = True`), secure flags are set to `False` so cookies can be transmitted over plain `http://`.

---

## Running Tests

The project includes an extensive automated test suite (30 test cases) distributed across dedicated test files:

### Test Modules

- **[`auth_app/tests.py`](file:///auth_app/tests.py)**:
  - `RegistrationTests`: Valid user registration, duplicate email rejection, password confirmation checks, and activation email dispatch.
  - `ActivationTests`: Account activation via base64 encoded user ID (`uidb64`) and token validation.
  - `LoginTests`: Credential verification, setting secure `HttpOnly` cookies (`access_token` and `refresh_token`), and inactive account rejection.
  - `TokenRefreshTests`: Renewing access tokens using HttpOnly refresh cookies and cookie clearing on invalid refresh attempts.
  - `LogoutTests`: Refresh token blacklisting and cookie removal.
  - `PasswordResetTests`: Token generation, email dispatch, and password confirmation with valid/invalid tokens.

- **[`video_app/tests.py`](file:///video_app/tests.py)**:
  - `VideoListApiTests`: Catalog listing, authentication enforcement, Redis response caching, cache invalidation on save/delete, and automatic thumbnail fallback when cleared.
  - `VideoPlaylistApiTests`: HLS master playlist delivery (`index.m3u8`), resolution validation (`480p`, `720p`, `1080p`), and 404 handling.
  - `VideoSegmentApiTests`: Binary MPEG-TS (`.ts`) video chunk streaming, content-type verification (`video/MP2T`), and boundary checks.

### Running the Tests

**Inside Docker (recommended):**

```bash
# Run all tests across the entire project
docker compose exec web python manage.py test

# Run tests in auth_app/tests.py
docker compose exec web python manage.py test auth_app.tests

# Run tests in video_app/tests.py
docker compose exec web python manage.py test video_app.tests
```

**Locally (outside Docker):**

```bash
# Run all tests with active virtual environment
python manage.py test
```
