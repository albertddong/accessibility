from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from urllib.parse import urlunsplit

from backend.config import settings
from backend.schemas import CreateGoogleDocRequest, CreateGoogleDocResponse
from backend.services.analysis import analyze_pdf_bytes
from backend.services.google_docs import (
    begin_google_oauth,
    build_post_auth_redirect,
    complete_google_oauth,
    create_google_doc,
    get_google_credentials,
    google_auth_status,
)


app = FastAPI(title="Accessibility Remediation API", version="0.1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site=settings.session_same_site,
    https_only=settings.session_cookie_secure,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/google-auth/status")
def google_auth_state(request: Request):
    return google_auth_status(request.session)


@app.get("/api/google-auth/start")
def google_auth_start(request: Request):
    auth_url = begin_google_oauth(request.session)
    if not auth_url:
        raise HTTPException(status_code=500, detail="Google credentials.json not found.")
    return RedirectResponse(auth_url)


@app.get("/api/google-auth/callback")
def google_auth_callback(request: Request):
    try:
        authorization_response = urlunsplit(
            (
                settings.public_backend_url.split("://", 1)[0],
                settings.public_backend_url.split("://", 1)[1].rstrip("/"),
                request.url.path,
                request.url.query,
                "",
            )
        )
        complete_google_oauth(request.session, authorization_response)
        return RedirectResponse(build_post_auth_redirect(True))
    except Exception as exc:
        return RedirectResponse(build_post_auth_redirect(False, str(exc)))


@app.post("/api/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    try:
        return analyze_pdf_bytes(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/create-google-doc", response_model=CreateGoogleDocResponse)
def create_doc(payload: CreateGoogleDocRequest, request: Request):
    try:
        credentials = get_google_credentials(request.session)
        if credentials is None:
            raise HTTPException(status_code=401, detail="Google account is not connected.")
        return create_google_doc(payload.analysis, credentials)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
