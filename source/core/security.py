from pwdlib import PasswordHash
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any, Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, UTC, timedelta, timezone
from source.core.config import setting
from source.models.user_model import User
from source.database.session import get_session
from jwt.exceptions import InvalidTokenError
import jwt

hash = PasswordHash.recommended()
authentication_schem = HTTPBearer()

def hash_password(password:str):
    return hash.hash(password=password)

def verify_password(user_password:str, hashed_password:str):
    return hash.verify(password=user_password, hash=hashed_password)

def create_access_token(user_data:dict[str, Any], expire:timedelta|None = None):
    user_data_copy = user_data.copy()
    if expire is None:
        expires = expires = datetime.now(UTC) + timedelta(setting.access_token_expires)
    else:
        expires = datetime.now(UTC) + expire
    user_data_copy.update({"exp": expires})
    return jwt.encode(user_data_copy, setting.access_token_secret.get_secret_value(), algorithm=setting.access_token_algorithm) #type:ignore

def decode_access_token(token:str):
    try:
        payload=jwt.decode(token, setting.access_token_secret.get_secret_value(), algorithms=[setting.access_token_algorithm])#type:ignore
        user, expired= payload.get("user"), payload.get("exp")
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid access token")
        if expired is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing expiration token")
        if datetime.now(UTC) > datetime.fromtimestamp(expired,tz=timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        return user
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user(user_data:Annotated[HTTPAuthorizationCredentials, Depends(authentication_schem)], db:Annotated[AsyncSession, Depends(get_session)]):
    user_data=decode_access_token(token=user_data.credentials)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found")
    user = await db.execute(select(User).where(User.id == user_data))
    existing_user = user.scalar_one_or_none()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return existing_user

protected = Annotated[User, Depends(get_current_user)]