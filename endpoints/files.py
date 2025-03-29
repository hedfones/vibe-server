import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from source import FileManager
from source.database import Photo
from source.utils import db

router = APIRouter()
file_manager = FileManager("booking-agent-dev")


def api_key_dependency(x_api_key: str = Header(...)):
    if not db.validate_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")


@router.post("/upload-file/", dependencies=[Depends(api_key_dependency)])
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    file_contents = await file.read()
    file_uid = file.filename  # You might want a unique naming scheme
    if not file_uid:
        raise HTTPException(400, "File must have a name.")
    if not file_manager.upload_file(file_uid, file_contents):
        raise HTTPException(500, "Failed to upload file.")
    return JSONResponse(content={"file_uid": file_uid, "message": "File uploaded successfully."})


@router.get("/read-file/{file_uid}", response_class=FileResponse, dependencies=[Depends(api_key_dependency)])
def read_file(file_uid: str) -> FileResponse:
    file_bytes = file_manager.get_file(file_uid)
    if file_bytes is None:
        raise HTTPException(404, f"File with UID {file_uid} not found.")
    tmp_file_path = Path("/tmp") / file_uid
    tmp_file_path.write_bytes(file_bytes)
    return FileResponse(tmp_file_path, filename=file_uid)


@router.post("/upload-photo/", dependencies=[Depends(api_key_dependency)])
async def upload_photo(file: UploadFile = File(...), description: str = None, x_api_key: str = Header(...)) -> Photo:
    file_contents = await file.read()
    file_uid = str(uuid.uuid4()) + Path(file.filename).suffix
    if not file_manager.upload_file(file_uid, file_contents):
        raise HTTPException(500, "Failed to upload photo.")
    if not description:
        temp_path = Path("/tmp") / file_uid
        temp_path.write_bytes(file_contents)
        from source.generative_ai_service import describe_image

        description = describe_image(temp_path)
    business = db.get_business_by_api_key(x_api_key)
    new_photo = Photo(file_uid=file_uid, description=description, business_id=business.id)
    db.insert_photos([new_photo])
    return new_photo
