# Accessibility Remediation App

This project now runs as a split architecture:

- `backend/`: FastAPI API for PDF analysis and Google Docs generation
- `frontend/`: React + Vite client with a glassmorphism UI
## Current Architecture

### Backend

The backend exposes:

- `POST /api/analyze`: uploads a PDF to Claude and returns structured figure/table analysis
- `POST /api/create-google-doc`: creates a formatted Google Doc from an analysis payload
- `GET /api/health`: simple health check

Backend responsibilities:

- Claude PDF analysis
- JSON validation
- table normalization for merged-cell style output
- Google Docs creation
- Google web OAuth session handling
- review-note insertion for flagged items

### Frontend

The frontend is a standalone React app focused on:

- PDF upload
- analysis review
- table preview
- page-number and confidence display
- Google Doc creation workflow
- Google account connection state

The UI follows the `agents/glassmorphism-SKILL.md` visual direction:

- translucent glass panels
- high-contrast typography
- bold enterprise layout
- accessible spacing and focus states

## Project Structure

```text
accessibility-rem/
├── Dockerfile
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── prompts.py
│   ├── schemas.py
│   └── services/
│       ├── analysis.py
│       ├── google_docs.py
│       └── tables.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── styles.css
├── requirements.txt
├── credentials.json        # optional local fallback only
└── .env
```

## Environment Setup

### Python backend

Install Python dependencies:

```bash
./venv/bin/pip install -r requirements.txt
```

Required environment variable in `.env`:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

Optional environment variables:

```bash
ANTHROPIC_MODEL=claude-sonnet-4-20250514
GOOGLE_OAUTH_CLIENT_CONFIG_JSON=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_CREDENTIALS_PATH=credentials.json
FRONTEND_ORIGIN=http://localhost:5173
FRONTEND_POST_AUTH_URL=http://localhost:5173
PUBLIC_BACKEND_URL=http://localhost:8000
SESSION_SECRET=replace-this-with-a-long-random-secret
SESSION_COOKIE_SECURE=false
SESSION_SAME_SITE=lax
ALLOW_INSECURE_OAUTH_TRANSPORT=true
```

### Frontend

Install frontend dependencies:

```bash
cd frontend
npm install
```

## Running The Refactored App

### 1. Start the backend

From the repo root:

```bash
npm run dev:backend
```

Backend runs at `http://localhost:8000`.

### 2. Start the frontend

In a second terminal:

```bash
npm run dev:frontend
```

Frontend runs at `http://localhost:5173`.

### 3. Verify the backend

Open:

```text
http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

## Google Docs Notes

Google Doc creation now uses a web-style OAuth flow driven by the backend.

For local development:

- clicking `Connect Google` sends the browser to the backend OAuth start route
- Google redirects back to the backend callback route
- the backend stores credentials in a server-side in-memory session store
- the backend then redirects the browser back to the frontend
- local HTTP OAuth requires:

```bash
ALLOW_INSECURE_OAUTH_TRANSPORT=true
```

For hosted deployment:

- create a Google OAuth client of type `Web application`, not `Desktop app`
- add an authorized redirect URI matching:

```text
https://your-backend-domain/api/google-auth/callback
```

- set:

```bash
FRONTEND_ORIGIN=https://your-frontend-domain
FRONTEND_POST_AUTH_URL=https://your-frontend-domain
PUBLIC_BACKEND_URL=https://your-backend-domain
SESSION_COOKIE_SECURE=true
SESSION_SAME_SITE=none
ALLOW_INSECURE_OAUTH_TRANSPORT=false
GOOGLE_CLIENT_ID=your-google-web-client-id
GOOGLE_CLIENT_SECRET=your-google-web-client-secret
```

Notes:

- the current session/token store is in-memory, so users will need to reconnect Google after a backend restart or redeploy
- for a serious production deployment, move session/token storage to a persistent store
- for Cloud Run or other hosted environments, prefer `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` or `GOOGLE_OAUTH_CLIENT_CONFIG_JSON` instead of shipping `credentials.json`

## Cloud Run Deployment

The backend is now container-ready via the root `Dockerfile`.

### 1. Create Google OAuth web credentials

In Google Cloud Console:

- create an OAuth client of type `Web application`
- add this authorized redirect URI:

```text
https://YOUR-CLOUD-RUN-URL/api/google-auth/callback
```

### 2. Deploy the backend to Cloud Run

From the repo root:

```bash
gcloud run deploy accessibility-rem-backend \
  --source . \
  --region us-east1 \
  --allow-unauthenticated
```

Set these environment variables in Cloud Run:

```bash
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
FRONTEND_ORIGIN=https://your-frontend-domain
FRONTEND_POST_AUTH_URL=https://your-frontend-domain
PUBLIC_BACKEND_URL=https://your-cloud-run-url
SESSION_SECRET=long-random-secret
SESSION_COOKIE_SECURE=true
SESSION_SAME_SITE=none
ALLOW_INSECURE_OAUTH_TRANSPORT=false
```

### 3. Deploy the frontend

Recommended frontend setup:

- deploy `frontend/` to Vercel
- set:

```bash
VITE_API_BASE_URL=https://your-cloud-run-url
```

## Migration Status

Implemented in the split app:

- PDF upload and Claude analysis
- page-number display in UI
- confidence and review flags
- normalized table preview
- Google Doc generation
- review note insertion into generated docs

Still to migrate or improve:

- CSV export in the new frontend
- anchored Google Docs comments instead of visible review notes only
- batch processing
- persistent token/session storage for hosted multi-user use
