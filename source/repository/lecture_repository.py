import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from source.models.lecture_model import (
    Assessment,
    Classroom,
    ClassroomMaterial,
    ClassroomMember,
    Submission,
)
from source.models.user_model import User


class LectureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.__session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------ classrooms
    async def join_code_exists(self, join_code: str) -> bool:
        result = await self.__session.execute(
            select(Classroom.id).where(Classroom.join_code == join_code)
        )
        return result.scalar_one_or_none() is not None

    async def add_classroom(self, classroom: Classroom) -> Classroom:
        self.__session.add(classroom)
        await self.__session.commit()
        await self.__session.refresh(classroom)
        return classroom

    async def get_classroom(self, classroom_id: uuid.UUID) -> Classroom | None:
        return await self.__session.get(Classroom, classroom_id)

    async def get_classroom_by_join_code(self, join_code: str) -> Classroom | None:
        result = await self.__session.execute(
            select(Classroom).where(Classroom.join_code == join_code)
        )
        return result.scalar_one_or_none()

    async def list_classrooms_owned_by(self, owner_id: uuid.UUID) -> list[Classroom]:
        result = await self.__session.execute(
            select(Classroom)
            .where(Classroom.owner_id == owner_id)
            .order_by(Classroom.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_classrooms_for_student(self, student_id: uuid.UUID) -> list[Classroom]:
        result = await self.__session.execute(
            select(Classroom)
            .join(ClassroomMember)
            .where(
                ClassroomMember.student_id == student_id,
                ClassroomMember.is_active.is_(True),
            )
            .order_by(Classroom.created_at.desc())
        )
        return list(result.scalars().all())

    async def save_classroom(self, classroom: Classroom) -> Classroom:
        await self.__session.commit()
        await self.__session.refresh(classroom)
        return classroom

    async def delete_classroom(self, classroom: Classroom) -> None:
        await self.__session.delete(classroom)
        await self.__session.commit()

    # ------------------------------------------------------------------ members
    async def get_membership(
        self, classroom_id: uuid.UUID, student_id: uuid.UUID
    ) -> ClassroomMember | None:
        result = await self.__session.execute(
            select(ClassroomMember)
            .where(
                ClassroomMember.classroom_id == classroom_id,
                ClassroomMember.student_id == student_id,
            )
            .options(selectinload(ClassroomMember.student))
        )
        return result.scalar_one_or_none()

    async def get_member_by_index_number(
        self, classroom_id: uuid.UUID, index_number: str
    ) -> ClassroomMember | None:
        result = await self.__session.execute(
            select(ClassroomMember)
            .where(
                ClassroomMember.classroom_id == classroom_id,
                ClassroomMember.index_number == index_number,
            )
            .options(selectinload(ClassroomMember.student))
        )
        return result.scalar_one_or_none()

    async def list_members(self, classroom_id: uuid.UUID) -> list[ClassroomMember]:
        result = await self.__session.execute(
            select(ClassroomMember)
            .where(ClassroomMember.classroom_id == classroom_id)
            .options(selectinload(ClassroomMember.student))
            .order_by(ClassroomMember.joined_at.asc())
        )
        return list(result.scalars().all())

    async def add_member(self, member: ClassroomMember) -> ClassroomMember:
        self.__session.add(member)
        await self.__session.commit()
        saved = await self.get_membership(member.classroom_id, member.student_id)
        if saved is None:  # pragma: no cover - defensive
            raise RuntimeError("Membership was not saved")
        return saved

    async def save_member(self, member: ClassroomMember) -> ClassroomMember:
        await self.__session.commit()
        saved = await self.get_membership(member.classroom_id, member.student_id)
        if saved is None:  # pragma: no cover - defensive
            raise RuntimeError("Membership disappeared while saving")
        return saved

    async def delete_member(self, member: ClassroomMember) -> None:
        await self.__session.delete(member)
        await self.__session.commit()

    # ------------------------------------------------------------------ materials
    async def add_material(self, material: ClassroomMaterial) -> ClassroomMaterial:
        self.__session.add(material)
        await self.__session.commit()
        await self.__session.refresh(material)
        return material

    async def get_material(self, material_id: uuid.UUID) -> ClassroomMaterial | None:
        return await self.__session.get(ClassroomMaterial, material_id)

    async def list_materials(self, classroom_id: uuid.UUID) -> list[ClassroomMaterial]:
        result = await self.__session.execute(
            select(ClassroomMaterial)
            .where(ClassroomMaterial.classroom_id == classroom_id)
            .order_by(ClassroomMaterial.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_material(self, material: ClassroomMaterial) -> None:
        await self.__session.delete(material)
        await self.__session.commit()

    # ------------------------------------------------------------------ assessments
    async def add_assessment(self, assessment: Assessment) -> Assessment:
        self.__session.add(assessment)
        await self.__session.commit()
        await self.__session.refresh(assessment)
        return assessment

    async def get_assessment(self, assessment_id: uuid.UUID) -> Assessment | None:
        return await self.__session.get(Assessment, assessment_id)

    async def list_assessments(self, classroom_id: uuid.UUID) -> list[Assessment]:
        result = await self.__session.execute(
            select(Assessment)
            .where(Assessment.classroom_id == classroom_id)
            .order_by(Assessment.due_date.asc())
        )
        return list(result.scalars().all())

    async def save_assessment(self, assessment: Assessment) -> Assessment:
        await self.__session.commit()
        await self.__session.refresh(assessment)
        return assessment

    async def delete_assessment(self, assessment: Assessment) -> None:
        await self.__session.delete(assessment)
        await self.__session.commit()

    # ------------------------------------------------------------------ submissions
    async def get_submission(self, submission_id: uuid.UUID) -> Submission | None:
        result = await self.__session.execute(
            select(Submission)
            .where(Submission.id == submission_id)
            .options(selectinload(Submission.student))
        )
        return result.scalar_one_or_none()

    async def get_submission_by_student(
        self, assessment_id: uuid.UUID, student_id: uuid.UUID
    ) -> Submission | None:
        result = await self.__session.execute(
            select(Submission)
            .where(
                Submission.assessment_id == assessment_id,
                Submission.student_id == student_id,
            )
            .options(selectinload(Submission.student))
        )
        return result.scalar_one_or_none()

    async def list_submissions(self, assessment_id: uuid.UUID) -> list[Submission]:
        result = await self.__session.execute(
            select(Submission)
            .where(Submission.assessment_id == assessment_id)
            .options(selectinload(Submission.student))
            .order_by(Submission.submitted_at.asc())
        )
        return list(result.scalars().all())

    async def add_submission(self, submission: Submission) -> Submission:
        self.__session.add(submission)
        await self.__session.commit()
        saved = await self.get_submission(submission.id)
        if saved is None:  # pragma: no cover - defensive
            raise RuntimeError("Submission was not saved")
        return saved
