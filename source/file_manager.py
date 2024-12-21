import logging
from typing import TypedDict
import boto3
from types_boto3_s3 import S3Client
from botocore.exceptions import ClientError

class File(TypedDict):
    uid: str
    filename: str

class FileManager:
    def __init__(self, bucket_name: str) -> None:
        self.s3_client: S3Client = boto3.client('s3')
        self.bucket_name: str = bucket_name

        # Check if the bucket exists
        if not self._does_bucket_exist():
            logging.info(f"Bucket '{self.bucket_name}' does not exist. Creating now.")
            _ = self.s3_client.create_bucket(Bucket=self.bucket_name)

    def _does_bucket_exist(self) -> bool:
        try:
            _ = self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            # The bucket does not exist or you have no access.
            return False

    def get_file(self, file_uid: str) -> bytes | None:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_uid)
            return response['Body'].read()
        except ClientError as e:
            logging.error(f"Error fetching file {file_uid} from bucket {self.bucket_name}: {e}")
            return None

    def upload_file(self, file_uid: str, file_data: bytes) -> bool:
        try:
            _ = self.s3_client.put_object(Bucket=self.bucket_name, Key=file_uid, Body=file_data)
            logging.info(f"File {file_uid} uploaded successfully to bucket {self.bucket_name}.")
            return True
        except ClientError as e:
            logging.error(f"Error uploading file {file_uid} to bucket {self.bucket_name}: {e}")
            return False
