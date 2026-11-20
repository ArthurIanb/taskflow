from pwdlib import PasswordHash

password_hash = PasswordHash().recommended()

def hash_password(pwd: str) -> str:
    return password_hash.hash(pwd)

def check_password(pwd: str, hashed_pwd: str) -> bool:
    return password_hash.verify(pwd, hashed_pwd)
