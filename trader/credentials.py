import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Credentials:
    api_key: str
    secret_key: str
    passphrase: str

    @property
    def display(self):
        return "(none)" if self.api_key is None else f"{self.api_key[0:6]}{'*' * 12}{self.api_key[-6:-1]}"

    def __str__(self):
        return self.display

    def __repr__(self):
        return self.display

    @classmethod
    def load_from_json(cls, path: Path) -> "Credentials":
        d = json.loads(path.read_text())
        return Credentials(api_key=d.get('api-key'),
                           secret_key=d.get('secret-key'),
                           passphrase=d.get('passphrase'))

    @classmethod
    def load_from_env(cls, prefix: str) -> "Credentials":
        import os
        return Credentials(api_key=os.getenv(f"{prefix}API_KEY"),
                           secret_key=os.getenv(f"{prefix}SECRET_KEY"),
                           passphrase=os.getenv(f"{prefix}PASSPHRASE"))

    @classmethod
    def load_from_vault(cls, token: str, namespace: str) -> "Credentials":
        # TODO: 从 vault 服务器获取
        return Credentials(api_key="", secret_key="", passphrase="")
