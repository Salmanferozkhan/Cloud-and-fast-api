"""Security utilities for password hashing using Argon2."""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Create password hasher with Argon2 (winner of Password Hashing Competition)
password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plain text password using Argon2.

    Args:
        password: Plain text password to hash.

    Returns:
        str: Argon2-hashed password string.
    """
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Argon2-hashed password to compare against.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return password_hash.verify(plain_password, hashed_password)
