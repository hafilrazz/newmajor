# NeuroLens — Clinical MRI Intelligence (Flask)

Professional **Flask-only** Alzheimer’s MRI workspace with a **premium enterprise UI** (Linear/Stripe-style marketing + clinical OS dashboard) + full API.

## Stack

- **UI:** Flask + Jinja2 + custom CSS (no Streamlit)
- **API:** Flask REST (`/api/*`)
- **ML:** PyTorch ResNet-18 · Grad-CAM
- **DB:** MongoDB (or in-memory mongomock fallback)

## Features

- Marketing home, about, contact
- User registration / login (admin demo: `admin` / `123456`)
- Dashboard with metrics & charts
- Patient registration → MRI prediction → Grad-CAM → assessment → AI report
- Patient history & population analytics
- PDF download + optional email

## Run (local)

```powershell
cd C:\newmajor
.\run_app.bat
```

Or:

```powershell
.\.venv\Scripts\python.exe -m backend.app
```

Open **http://127.0.0.1:5000**

## Run (Docker)

Requires `models/model.pth` on the host.

```powershell
cd C:\newmajor
copy .env.example .env   # first time only; edit secrets as needed
docker compose up --build
```

| Service | URL |
|---------|-----|
| **NeuroLens app (UI + API)** | http://localhost:5000 |
| MongoDB | localhost:27017 |
| Mailpit (test email UI) | http://localhost:8025 |
| Mailpit SMTP | localhost:1025 |

Stop:

```powershell
docker compose down
```

### Docker layout

- **`web`** — Flask app (`backend/Dockerfile`): Jinja UI, `/api/*`, PyTorch inference  
- **`mongo`** — patient / prediction storage  
- **`mailpit`** — optional local SMTP for report emails  

The old Streamlit frontend container is **removed**; everything is served from port **5000**.

## Layout

```
backend/
  app.py              # Flask app (UI + API)
  Dockerfile          # production image for compose `web`
  templates/          # Jinja pages
  static/             # CSS / JS
  web/routes.py       # HTML routes
  routes/             # JSON API
  services/           # ML + reports
models/model.pth
docker-compose.yml
```

## API (same process as the UI)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/auth/login` | Login |
| `POST /api/patients/register` | Register patient |
| `POST /api/predictions` | MRI prediction |
| `GET /api/analytics/*` | Analytics |
| `POST /api/reports/generate` | Report |

## Clinical disclaimer

Decision-support prototype for education/research — **not** a diagnostic device.
