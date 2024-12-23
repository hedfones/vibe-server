import json
import logging

import boto3
from botocore.exceptions import ClientError
from types_boto3_secretsmanager import SecretsManagerClient


class SecretsManager:
    """A class to manage secrets using AWS Secrets Manager."""

    def __init__(self):
        """
        Initializes SecretsManager with AWS Secrets Manager.

        Args:
            region_name (str): The AWS region where the secrets are stored.
        """
        self.client: SecretsManagerClient = boto3.client("secretsmanager")

    def get_secret(self, secret_name: str) -> dict[str, str]:
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
            logging.error(f"Failed to retrieve secret {secret_name}: {e}")
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
            secret_body = self.get_secret(secret_name)
            return secret_body.get(key)
        except RuntimeError as e:
            raise ValueError from e


if __name__ == "__main__":
    sm = SecretsManager()
    print(sm.get("POSTGRES_PORT"))
