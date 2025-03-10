from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str) -> str:
    time_now = datetime.now(timezone.utc)
    expire = time_now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    jwt_claims = {
        "iss": str(settings.SERVER_HOST),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "sub": subject,
    }

    encoded_jwt = jwt.encode(
        jwt_claims,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def verify_access_token(token: str) -> Dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
