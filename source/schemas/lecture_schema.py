from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator


class AssessmentType(str, Enum):
    assignment = "assignment"
    quiz = "quiz"


MemberName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
IndexNumber = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50, to_upper=True)
]


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserSummary(ORMBase):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr


class ClassroomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ClassroomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    regenerate_join_code: bool = False


class ClassroomResponse(ORMBase):
    id: uuid.UUID
    name: str
    join_code: str
    owner_id: uuid.UUID
    created_at: datetime


class JoinClassroom(BaseModel):
    join_code: str = Field(min_length=4, max_length=12)
    name: MemberName | None = None
    index_number: IndexNumber


class AddStudent(BaseModel):
    email: EmailStr
    name: MemberName | None = None
    index_number: IndexNumber


class UpdateStudent(BaseModel):
    name: MemberName | None = None
    index_number: IndexNumber | None = None
    is_active: bool | None = None


class ClassroomMemberResponse(ORMBase):
    id: uuid.UUID
    classroom_id: uuid.UUID
    student_id: uuid.UUID
    name: str
    index_number: str
    is_active: bool
    joined_at: datetime
    student: UserSummary


class MaterialResponse(ORMBase):
    id: uuid.UUID
    classroom_id: uuid.UUID
    uploaded_by_id: uuid.UUID
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime


class AssessmentCreate(BaseModel):
    type: AssessmentType
    title: str = Field(min_length=1, max_length=150)
    description: str | None = None
    due_date: datetime

    @field_validator("due_date")
    @classmethod
    def _ensure_timezone(cls, value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)


class AssessmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    due_date: datetime | None = None

    @field_validator("due_date")
    @classmethod
    def _ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return value if value.tzinfo else value.replace(tzinfo=UTC)


class AssessmentResponse(ORMBase):
    id: uuid.UUID
    classroom_id: uuid.UUID
    created_by_id: uuid.UUID
    type: AssessmentType
    title: str
    description: str | None
    due_date: datetime
    created_at: datetime


class SubmissionResponse(ORMBase):
    id: uuid.UUID
    assessment_id: uuid.UUID
    student_id: uuid.UUID
    text_answer: str | None
    original_name: str | None
    content_type: str | None
    size_bytes: int | None
    submitted_at: datetime
    is_late: bool
    student: UserSummary
