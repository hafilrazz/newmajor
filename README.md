# NeuroLens — Clinical Multi-Modal Intelligence Platform (Flask)

Professional **Flask-only** Alzheimer’s clinical decision-support workspace with an **enterprise Volt UI** + full REST API.

## Stack

- **UI:** Flask + Jinja2 + custom CSS (Volt design system)
- **API:** Flask REST (`/api/predictions/*`, `/api/patients/*`, `/api/reports/*`, `/api/analytics/*`)
- **ML / AI Models:**
  - **MRI Intelligence:** PyTorch ResNet-18 (4-class) + Grad-CAM++ with multi-layer fusion
  - **CT Stacking Ensemble:** MobileNetV2 + EfficientNet-B0 + Meta-Neural-Network (4-class) + Grad-CAM
  - **Clinical Stacking Ensemble:** Random Forest (10 features) + XGBoost (32 features) with Soft Average consensus
- **DB:** MongoDB (with automatic in-memory mongomock fallback & durable JSON backup)

## Features

- Marketing home, about, contact
- User registration / login (admin demo: `admin` / `123456`)
- Dashboard with cohort metrics & interactive charts
- **Independent Clinical Pathways:**
  - **MRI Prediction** (`/app/mri`) → Grad-CAM++ overlay → deletion faithfulness test
  - **CT Scan Prediction** (`/app/ct`) → Stacking Ensemble consensus + CT Grad-CAM
  - **Clinical Assessment** (`/app/clinical`) → 32 biomarkers → Random Forest + XGBoost soft average risk score
- State isolation across modalities (zero cross-contamination)
- Clinical assessment recording & longitudinal history tracking
- Automated PDF report generation (ReportLab) + SMTP email dispatch

## installation and Run (local)

```powershell
cd C:\newmajor

py -3.13 -m venv .venv                                                                       
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r frontend\requirements.txt

(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\newmajor\.venv\Scripts\Activate.ps1)

.\run_app.bat
```

Or:

```powershell
.\.venv\Scripts\python.exe -m backend.app
```

Open **http://127.0.0.1:5000**

## Run (Docker)

Requires `models/model.pth` on the host. Serves the **Volt-style Flask UI + API** on one port.

```powershell
cd C:\newmajor
copy .env.example .env   # optional; edit secrets as needed
docker compose up --build
```

| Service | URL |
|---------|-----|
| **NeuroLens app (Volt UI + API)** | http://localhost:5000 |
| MongoDB | localhost:27017 |
| Mailpit (test email UI) | http://localhost:8025 |
| Mailpit SMTP | localhost:1025 |

Rebuild only the app after UI changes:

```powershell
docker compose up --build web
```

Stop:

```powershell
docker compose down
```

### Docker layout

| File | Purpose |
|------|---------|
| `backend/Dockerfile` | Production image (Flask Volt UI + API + model) |
| `Dockerfile` | Same image, buildable from repo root |
| `docker-compose.yml` | `web` + `mongo` + `mailpit` |

- **`web`** — gunicorn on port 5000 (`backend.wsgi:app`)  
- **`mongo`** — patient / prediction storage  
- **`mailpit`** — local SMTP for AI report emails  

Streamlit is **not** used. Everything is on **port 5000**.

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
| `POST /api/predictions` | MRI prediction (ResNet-18) |
| `POST /api/predictions/ct` | CT scan prediction (Stacking Ensemble) |
| `POST /api/predictions/clinical` | Clinical assessment (RF + XGBoost Soft Average) |
| `GET /api/analytics/*` | Analytics & Cohort Distribution |
| `POST /api/reports/generate` | Generate PDF Clinical Report |
| `POST /api/reports/email` | Email Clinical Report via SMTP |

## Clinical disclaimer

Decision-support prototype for education/research — **not** a diagnostic device.
