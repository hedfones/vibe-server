import structlog
from fastapi import APIRouter, Header, HTTPException

from source.utils import db

log = structlog.stdlib.get_logger()
router = APIRouter()


def api_key_dependency(x_api_key: str = Header(...)):
    if not db.validate_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")
