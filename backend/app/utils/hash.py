from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_pwd(pwd: str) -> str:
    return pwd_context.hash(pwd) 
    
def verify_pwd(pwd: str, hashed_pwd: str) -> bool:
    return pwd_context.verify(pwd, hashed_pwd)