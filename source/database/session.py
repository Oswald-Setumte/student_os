from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from source.core.config import setting

engine = create_async_engine(setting.database_url)
local_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with local_session() as session:
        yield session

