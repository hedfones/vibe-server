from os import PathLike


class SecretsManager:
    """A class to manage secrets stored in a .envrc file.

    Attributes:
        env_file (str): The path to the .envrc file.
        secrets (dict): A dictionary containing the loaded secrets.
    """

    def __init__(self, env_file: PathLike = ".envrc"):
        """Initializes SecretsManager with the specified environment file.

        Args:
            env_file (str): The path to the .envrc file. Defaults to '.envrc'.
        """
        self.env_file = env_file
        self.secrets = self.load_secrets()

    def load_secrets(self) -> dict:
        """Loads secrets from the specified .envrc file.

        Returns:
            dict: A dictionary containing the loaded secrets.
        """
        secrets = {}
        try:
            with open(self.env_file) as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue
                    key, value = line.strip().split("=", 1)
                    value = value.strip('"')
                    secrets[key] = value
        except FileNotFoundError:
            print(f"Warning: {self.env_file} not found. No secrets loaded.")
        return secrets

    def get(self, key: str) -> str | None:
        """Retrieves the value of a secret by its key.

        Args:
            key (str): The key of the secret to retrieve.

        Returns:
            str: The value of the secret, or None if not found.
        """
        return self.secrets.get(key)

    def update_secret(self, key: str, value: str) -> None:
        """Updates a secret with the given key and value.

        Args:
            key (str): The key of the secret to update.
            value (str): The new value for the secret.
        """
        self.secrets[key] = value
        self.save_secrets()

    def save_secrets(self) -> None:
        """Saves the current secrets back to the .envrc file."""
        with open(self.env_file, "w") as f:
            for key, value in self.secrets.items():
                f.write(f"{key}={value}\n")


secret_manager = SecretsManager()
