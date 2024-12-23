import logging
from typing import TypedDict

import boto3
from botocore.exceptions import ClientError
from types_boto3_s3 import S3Client


class File(TypedDict):
    """
    A typed dictionary representing a file with a unique identifier and filename.

    Attributes:
        uid (str): Unique identifier for the file.
        filename (str): Name of the file.
    """

    uid: str
    filename: str


class FileManager:
    """
    Manages file operations in an S3 bucket, including uploading and retrieving files.

    Attributes:
        s3_client (S3Client): The Boto3 S3 client used to interact with S3.
        bucket_name (str): Name of the S3 bucket.
    """

    def __init__(self, bucket_name: str) -> None:
        """
        Initializes the FileManager with the specified S3 bucket.

        Args:
            bucket_name (str): The name of the S3 bucket to manage.
        """
        self.s3_client: S3Client = boto3.client("s3")
        self.bucket_name: str = bucket_name

        # Check if the bucket exists
        if not self._does_bucket_exist():
            logging.info(f"Bucket '{self.bucket_name}' does not exist. Creating now.")
            # Attempt to create the bucket
            _ = self.s3_client.create_bucket(Bucket=self.bucket_name)

    def _does_bucket_exist(self) -> bool:
        """
        Checks if the S3 bucket exists and is accessible.

        Returns:
            bool: True if the bucket exists and is accessible, False otherwise.
        """
        try:
            # Attempt to get the bucket's metadata
            _ = self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            # The bucket does not exist or access is denied.
            return False

    def get_file(self, file_uid: str) -> bytes | None:
        """
        Retrieves a file from the S3 bucket.

        Args:
            file_uid (str): The unique identifier of the file to retrieve.

        Returns:
            bytes | None: The file data as bytes if successful, None otherwise.
        """
        try:
            # Attempt to get the specified object from the S3 bucket
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_uid)
            return response["Body"].read()
        except ClientError as e:
            logging.error(f"Error fetching file {file_uid} from bucket {self.bucket_name}: {e}")
            return None

    def upload_file(self, file_uid: str, file_data: bytes) -> bool:
        """
        Uploads a file to the S3 bucket.

        Args:
            file_uid (str): The unique identifier for the file.
            file_data (bytes): The file data to upload.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        try:
            # Attempt to upload the object to the S3 bucket
            _ = self.s3_client.put_object(Bucket=self.bucket_name, Key=file_uid, Body=file_data)
            logging.info(f"File {file_uid} uploaded successfully to bucket {self.bucket_name}.")
            return True
        except ClientError as e:
            logging.error(f"Error uploading file {file_uid} to bucket {self.bucket_name}: {e}")
            return False
