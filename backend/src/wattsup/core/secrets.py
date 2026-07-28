import base64
import hashlib

from cryptography.fernet import Fernet


class SecretBox:
    def __init__(self, secret: str) -> None:
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        self.fernet = Fernet(key)

    def encrypt(self, value: str | None) -> str | None:
        return self.fernet.encrypt(value.encode()).decode() if value else None

    def decrypt(self, value: str | None) -> str | None:
        return self.fernet.decrypt(value.encode()).decode() if value else None
