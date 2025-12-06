import bcrypt
import hashlib

from rich import panel, print


def hash_password(password: str) -> str:
    """
    Hashes a password using SHA-256 pre-hash + bcrypt.
    Returns a UTF-8 string ready to store in DB.
    """
    # print(panel.Panel(f"Password:{password}", border_style="green"))

    password_bytes = password.encode("utf-8")
    # Pre-hash to avoid bcrypt 72-byte limit
    password_bytes = hashlib.sha256(password_bytes).digest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plaintext password against the hashed value from DB
    """
    password_bytes = password.encode("utf-8")
    password_bytes = hashlib.sha256(password_bytes).digest()
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
