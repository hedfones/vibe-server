import os

import requests
import structlog
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from source.utils import db

log = structlog.stdlib.get_logger()
router = APIRouter()


def api_key_dependency(x_api_key: str = Header(...)):
    if not db.validate_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")


@router.post("/distil/", dependencies=[Depends(api_key_dependency)])
async def perform_distillation_upload(
    pdf_files: list[UploadFile] = File(...),
    audio_file: UploadFile = File(...),
    business_name: str = Form(...),
    additional_write_instructions: str = Form(...),
    x_api_key: str = Header(...),
) -> dict[str, str]:
    # TODO: Test this crap

    # Build the remote URL.
    remote_url = f"{os.environ['ADMIN_SERVER_URL']}/distil_upload/"

    # Construct the list of tuples for multiple PDF files.
    # Each tuple follows the form:
    #   (field_name, (filename, file-object, content_type))
    pdf_files_list = [("pdf_files", (pdf.filename, pdf.file, pdf.content_type)) for pdf in pdf_files]

    # Build the tuple for the audio file.
    audio_file_tuple = ("audio_file", (audio_file.filename, audio_file.file, audio_file.content_type))

    # Build the form data for the non-file fields.
    data = {
        "business_name": business_name,
        "additional_write_instructions": additional_write_instructions,
    }

    # Combine all files (the API expects 'pdf_files' as a list and 'audio_file' as a separate field)
    files = tuple(pdf_files_list + [audio_file_tuple])

    try:
        response = requests.post(remote_url, files=files, data=data)
    except Exception as exc:
        log.exception("Error calling the remote distillation endpoint", exc_info=exc)
        raise HTTPException(status_code=500, detail="Error communicating with distillation service") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    # Optionally, close the opened file pointers.
    for pdf in pdf_files:
        pdf.file.close()
    audio_file.file.close()

    return response.json()
