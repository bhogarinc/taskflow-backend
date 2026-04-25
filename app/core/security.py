"""
Security Utilities.

Password hashing, JWT token generation and verification.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.schemas.token import TokenPayload

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, UUID],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(
    subject: Union[str, UUID],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT refresh token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        user_id = payload.get("sub")
        exp = payload.get("exp")
        token_type = payload.get("type")
        
        if user_id is None or exp is None:
            return None
        
        exp_datetime = datetime.fromtimestamp(exp)
        if datetime.utcnow() > exp_datetime:
            return None
        
        return TokenPayload(
            sub=UUID(user_id) if user_id else None,
            exp=exp_datetime,
            type=token_type,
        )
    except (JWTError, ValueError):
        return None


def verify_refresh_token(token: str) -> Optional[UUID]:
    """Verify refresh token and return user_id."""
    payload = decode_token(token)
    if payload is None or payload.type != "refresh":
        return None
    return payload.sub