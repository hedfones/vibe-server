import json
import os

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

# Add these variables to fetch credentials and define scopes
GOOGLE_REDIRECT_URI = os.environ["SERVER_BASE_URL"] + "/auth/google/callback/"
SECRET_NAME = "GOOGLE_CLIENT_KEY_SECRET_VIBE"

# Initialize OAuth2 flow
client_key_secret = secrets.get_raw(SECRET_NAME)
flow = InstalledAppFlow.from_client_config(client_key_secret, SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
log.info("Credentials obtained from OAuth flow.")


@router.get("/google/{organization_id}")  # Change to use organization_id in the path
async def google_auth(organization_id: str):
    state = json.dumps({"organization_id": organization_id})
    authorization_url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=state)
    return RedirectResponse(authorization_url)


@router.get("/google/callback/")
async def google_callback(code: str, state: str):
    # Fetch the token using the authorization code
    _ = flow.fetch_token(code=code, client_secret=client_key_secret["installed"]["client_secret"])
    credentials = flow.credentials  # This is a Credentials object

    state_data: dict[str, int] = json.loads(state)
    business = db.get_business_by_id(state_data["organization_id"])
    if business is None:
        raise HTTPException(404, detail="Business not found.")

    secrets.update(f"GOOGLE_OAUTH2_{business.calendar_service_id}", "token", credentials.to_json())

    db.update_business(business.id, {"calendar_service_authenticated": True})

    # Redirect or return a success response
    return {"message": "Google authentication successful."}
