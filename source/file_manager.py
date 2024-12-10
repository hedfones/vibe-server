import logging
from pathlib import Path
from typing import TypedDict


class File(TypedDict):
    uid: str
    filename: str


class FileManager:
    def __init__(self, files_directory: Path | str = "./files") -> None:
        self.file_store_path: Path = Path(files_directory)

        if not self.file_store_path.exists():
            logging.info(f"File store at {self.file_store_path} does not exist. Creating now.")
            self.file_store_path.mkdir(parents=True)

    def get_file(self, file_uid: str) -> Path:
        file = next(self.file_store_path.glob(f"{file_uid}*"))
        return file
