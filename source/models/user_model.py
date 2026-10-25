from source.database.base import Base
from sqlalchemy import Uuid, DateTime, String, Enum
from source.schemas.user_schema import Role
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, UTC
import uuid 


class User(Base):
    __tablename__ = "user"
    id:Mapped[uuid.UUID]=mapped_column(Uuid(as_uuid=True), primary_key=True, default=lambda:uuid.uuid4(), index=True)
    first_name:Mapped[str]=mapped_column(String(50), nullable=False, unique=True)
    last_name:Mapped[str]=mapped_column(String(50), nullable=False, unique=True)
    email:Mapped[str]=mapped_column(String(255), nullable=False, unique=True)
    password:Mapped[str]=mapped_column(String(255), nullable=False)
    role:Mapped[Role]=mapped_column(Enum(Role, name="role"), nullable=False, default=Role.student)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False, default=lambda:datetime.now(UTC))
