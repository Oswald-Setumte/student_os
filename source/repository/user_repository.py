from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from source.models.user_model import User

class UserRepository():
    def __init__(self, sesssion:AsyncSession):
        self.__session = sesssion

    async def get_user_by_email(self, query:str)->User|None:
        result = await self.__session.execute(select(User).where(User.email == query))
        user = result.scalar_one_or_none()
        return user

    async def add_user_to_database(self, user:User):
        self.__session.add(user)
        await self.__session.commit()
        await self.__session.refresh(user)
        return user

    @property
    async def get_all_user(self):
        users = await self.__session.execute(select(User))
        return users.scalars().all()

    