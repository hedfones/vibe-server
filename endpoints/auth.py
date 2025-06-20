import base64
import json
import os
import pickle

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import InstalledAppFlow

from source import SecretsManager
from source.google_service.auth import SCOPES
from source.utils import db

log = structlog.stdlib.get_logger()
router = APIRouter()
secrets = SecretsManager()

GOOGLE_REDIRECT_URI = os.environ["SERVER_BASE_URL"] + "/auth/google/callback/"
SECRET_NAME = "GOOGLE_CLIENT_KEY_SECRET_VIBE"

client_key_secret = secrets.get_raw(SECRET_NAME)
flow = InstalledAppFlow.from_client_config(client_key_secret, SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
log.info("Credentials obtained from OAuth flow.")


@router.get("/google/{organization_id}")
async def google_auth(organization_id: str):
    business = db.get_business_by_id(int(organization_id))
    if not business:
        raise HTTPException(404, detail="Business not found.")
    if business.calendar_service_authenticated:
        raise HTTPException(400, detail="Google Calendar service already authenticated.")
    state = json.dumps({"organization_id": organization_id})
    authorization_url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=state)
    return RedirectResponse(authorization_url)


@router.get("/google/callback/")
async def google_callback(code: str, state: str):
    _ = flow.fetch_token(code=code, client_secret=client_key_secret["web"]["client_secret"])
    credentials = flow.credentials
    state_data: dict[str, int] = json.loads(state)
    business = db.get_business_by_id(state_data["organization_id"])
    if business is None:
        raise HTTPException(404, detail="Business not found.")

    token_pickle = pickle.dumps(credentials)
    token_encoded = base64.b64encode(token_pickle).decode("utf-8")
    secrets.update(f"GOOGLE_OAUTH2_{business.calendar_service_id}", "token", token_encoded)
    db.update_business(business.id, {"calendar_service_authenticated": True})
    return {"message": "Google authentication successful."}
