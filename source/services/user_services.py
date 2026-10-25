from source.repository.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from source.models.user_model import User
from source.core.security import hash_password, verify_password, create_access_token
from source.schemas.user_schema import Register_user, Login_response
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

class UserServices():
    def __init__(self, session:AsyncSession) -> None:
        self.__services = UserRepository(sesssion=session)

    async def register_user(self, user:Register_user):
        existing_user = await self.__services.get_user_by_email(query=user.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already registered")
        new_user= User(
            **Register_user(
                first_name= user.first_name,
                last_name= user.last_name,
                email= user.email,
                password= hash_password(user.password),
                role= user.role
            ).model_dump()
            )
        return await self.__services.add_user_to_database(user=new_user)

    async def log_in_user(self, user:OAuth2PasswordRequestForm):
        existing_user = await self.__services.get_user_by_email(query=user.username)
        if not existing_user  or not verify_password(user_password=user.password, hashed_password=existing_user.password):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invaild cridentials, check your email or password")
        token = create_access_token(user_data={"user":str(existing_user.id)})
        return Login_response(token=token, type="baerer")

    async def get_me(self, user:str)->User|None:
        return await self.__services.get_user_by_email(query=user)

    @property
    async def get_all_users(self):
        return await self.__services.get_all_user