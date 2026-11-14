from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from source.database.base import Base
from source.models.user_model import User
from source.schemas.lecture_schema import AssessmentType


class Classroom(Base):
    __tablename__ = "classroom"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=lambda: uuid.uuid4()
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    join_code: Mapped[str] = mapped_column(String(12), nullable=False, unique=True, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    owner: Mapped[User] = relationship()
    members: Mapped[list[ClassroomMember]] = relationship(
        back_populates="classroom", cascade="all, delete-orphan"
    )
    materials: Mapped[list[ClassroomMaterial]] = relationship(
        back_populates="classroom", cascade="all, delete-orphan"
    )
    assessments: Mapped[list[Assessment]] = relationship(
        back_populates="classroom", cascade="all, delete-orphan"
    )


class ClassroomMember(Base):
    __tablename__ = "classroom_member"
    __table_args__ = (
        UniqueConstraint("classroom_id", "student_id", name="uq_classroom_member_classroom_student"),
        UniqueConstraint(
            "classroom_id", "index_number", name="uq_classroom_member_classroom_index_number"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=lambda: uuid.uuid4()
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classroom.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    index_number: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    classroom: Mapped[Classroom] = relationship(back_populates="members")
    student: Mapped[User] = relationship()


class ClassroomMaterial(Base):
    __tablename__ = "classroom_material"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=lambda: uuid.uuid4()
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classroom.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False, default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    classroom: Mapped[Classroom] = relationship(back_populates="materials")
    uploader: Mapped[User] = relationship()


class Assessment(Base):
    __tablename__ = "assessment"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=lambda: uuid.uuid4()
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classroom.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[AssessmentType] = mapped_column(
        Enum(AssessmentType, name="assessment_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    classroom: Mapped[Classroom] = relationship(back_populates="assessments")
    creator: Mapped[User] = relationship()
    submissions: Mapped[list[Submission]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class Submission(Base):
    __tablename__ = "submission"
    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", name="uq_submission_assessment_student"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, index=True, default=lambda: uuid.uuid4()
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stored_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    assessment: Mapped[Assessment] = relationship(back_populates="submissions")
    student: Mapped[User] = relationship()
