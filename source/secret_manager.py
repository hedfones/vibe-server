import os


class SecretsManager:
    """A class to manage secrets using environment variables.

    Attributes:
        secrets (dict): A dictionary containing the loaded secrets.
    """

    def __init__(self):
        """Initializes SecretsManager with the current environment variables."""
        self.secrets: dict[str, str] = self.load_secrets()

    def load_secrets(self) -> dict[str, str]:
        """Loads secrets from the environment variables.

        Returns:
            dict: A dictionary containing the loaded secrets.
        """
        return dict(os.environ)

    def get(self, key: str) -> str:
        """Retrieves the value of a secret by its key.

        Args:
            key (str): The key of the secret to retrieve.

        Returns:
            str: The value of the secret, or None if not found.
        """
        return self.secrets[key]


secret_manager = SecretsManager()
