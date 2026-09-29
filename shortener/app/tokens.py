import hashlib
import hmac
import secrets


def new_delete_token() -> tuple[str, str]:
    """Returns (raw_token_for_client, hash_for_database)."""
    token = secrets.token_urlsafe(32)  # 32 random bytes -> 43 chars
    return token, hash_token(token)


def hash_token(token: str) -> str:
    # SHA-256, not bcrypt: the token is 256 random bits, so it can't be
    # brute-forced. Slow hashing only matters for low-entropy passwords.
    return hashlib.sha256(token.encode()).hexdigest()  # always 64 hex chars


def verify_token(token: str, stored_hash: str) -> bool:
    # compare_digest takes the same time wherever the mismatch is,
    # so response timing leaks nothing about the correct hash.
    return hmac.compare_digest(hash_token(token), stored_hash)
