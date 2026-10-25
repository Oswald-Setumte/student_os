from fastapi import APIRouter,Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from source.schemas.user_schema import Register_user, Register_user_response,Login_response
from source.database.session import get_session
from source.services.user_services import UserServices
from source.core.security import protected


router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/register", response_model=Register_user_response)
async def create_user(user:Register_user, db:Annotated[AsyncSession, Depends(get_session)]):
    services = UserServices(session=db)
    register = await services.register_user(user=user)
    return register

@router.post("/login", response_model=Login_response)
async def login(user:Annotated[OAuth2PasswordRequestForm, Depends()], db:Annotated[AsyncSession, Depends(get_session)]):
    services = UserServices(session=db)
    login = await services.log_in_user(user=user)
    return login

@router.get("/me", response_model=Register_user_response)
async def me(user:protected, db:Annotated[AsyncSession, Depends(get_session)]):
    if user:
        services = UserServices(session=db)
        return await services.get_me(user=user.email)
        
@router.get("/all_user", response_model=list[Register_user_response])
async def all_users(user:protected, db:Annotated[AsyncSession, Depends(get_session)]):
    if user:
        services = UserServices(session=db)
        return await services.get_all_users
    else:
        raise "oswald"

