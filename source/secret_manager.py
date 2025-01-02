import json
from typing import Callable

import boto3
import structlog
from botocore.exceptions import ClientError
from types_boto3_secretsmanager import SecretsManagerClient

log = structlog.stdlib.get_logger()
JsonableType = str | int | float | bool | None | dict[str, "JsonableType"] | list["JsonableType"]


class SecretsManager:
    """A class to manage secrets using AWS Secrets Manager."""

    def __init__(self):
        """
        Initializes SecretsManager with AWS Secrets Manager.

        Args:
            region_name (str): The AWS region where the secrets are stored.
        """
        self.client: SecretsManagerClient = boto3.client("secretsmanager")

    def get_raw(self, secret_name: str) -> dict[str, JsonableType]:
        """
        Retrieves the secret value for the given secret name.

        Args:
            secret_name (str): The name of the secret to retrieve.

        Returns:
            dict: The secret value payload

        Raises:
            RuntimeError: If the secret cannot be retrieved.
        """
        try:
            get_secret_value_response = self.client.get_secret_value(SecretId=secret_name)

            # Decrypts and returns the secret as a dictionary
            if secret_string := get_secret_value_response.get("SecretString"):
                return json.loads(secret_string)
            else:
                return {}

        except ClientError as e:
            log.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise RuntimeError(f"Failed to retrieve secret {secret_name}") from e

    def get(self, secret_name: str, key: str | None = None) -> str:
        """
        Retrieves the value of a specific key from a secret.

        Args:
            secret_name (str): The name of the secret.
            key (str): The key of the secret. If not set, then will use secret
            name as the key.

        Returns:
            str: The value of the secret key
        """
        if not key:
            key = secret_name
        try:
            secret_body = self.get_raw(secret_name)
            if isinstance(secret_body[key], dict):
                return json.dumps(secret_body[key])
            return str(secret_body[key])
        except RuntimeError as e:
            raise ValueError from e

    def update(self, secret_name: str, key: str | None, value: JsonableType) -> None:
        """
        Updates the secret value for the given secret name.

        Args:
            secret_name (str): The name of the secret to update.
            secret_value (str): The new value for the secret.
        """
        try:
            body = self.get_raw(secret_name)
            if not key:
                key = secret_name
            body[key] = value
            _ = self.client.update_secret(SecretId=secret_name, SecretString=json.dumps(body))
            log.info(f"Updated secret {secret_name}")
        except ClientError as e:
            log.error(f"Failed to update secret {secret_name}: {e}")
            raise RuntimeError(f"Failed to update secret {secret_name}") from e

    def get_update_callback(self, secret_name: str) -> Callable[[str, JsonableType], None]:
        def wrapper(secret_key: str, secret_value: JsonableType) -> None:
            self.update(secret_name, secret_key, secret_value)

        return wrapper


if __name__ == "__main__":
    sm = SecretsManager()
    print(sm.get("POSTGRES_PORT"))
