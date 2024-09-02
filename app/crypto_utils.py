import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# 定数（Saltの長さと反復数）
SALT_LENGTH = 16
ITERATIONS = 100000


def generate_salt() -> str:
    """ランダムなSaltを生成"""
    salt = os.urandom(SALT_LENGTH)
    return base64.urlsafe_b64encode(salt).decode()


def get_key_from_password(password: str, salt: str) -> bytes:
    """パスワードとSaltからキーを導出"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=base64.urlsafe_b64decode(salt),
        iterations=ITERATIONS,
        backend=default_backend(),
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_token(token: str, password: str, salt: str) -> str:
    """アクセストークンを暗号化する"""
    key = get_key_from_password(password, salt)
    cipher_suite = Fernet(key)
    encrypted_token = cipher_suite.encrypt(token.encode())
    return encrypted_token.decode("utf-8")


def decrypt_token(encrypted_token: str, password: str, salt: str) -> str:
    """暗号化されたトークンを復号化する"""
    key = get_key_from_password(password, salt)
    cipher_suite = Fernet(key)
    decrypted_token = cipher_suite.decrypt(encrypted_token.encode())
    return decrypted_token.decode("utf-8")
