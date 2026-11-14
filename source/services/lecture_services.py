import secrets
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from source.core.config import setting
from source.models.lecture_model import (
    Assessment,
    Classroom,
    ClassroomMaterial,
    ClassroomMember,
    Submission,
)
from source.models.user_model import User
from source.repository.lecture_repository import LectureRepository
from source.schemas.lecture_schema import (
    AddStudent,
    AssessmentCreate,
    AssessmentUpdate,
    ClassroomCreate,
    ClassroomUpdate,
    JoinClassroom,
    UpdateStudent,
)
from source.schemas.user_schema import Role


class LectureService:
    JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    JOIN_CODE_LENGTH = 8
    CHUNK_SIZE = 1024 * 1024

    def __init__(self, session: AsyncSession) -> None:
        self.__repo = LectureRepository(session=session)
        self.__upload_root = Path(setting.upload_dir).resolve() / "classrooms"

    # ------------------------------------------------------------------ helpers
    async def _new_join_code(self) -> str:
        for _ in range(10):
            code = "".join(
                secrets.choice(self.JOIN_CODE_ALPHABET) for _ in range(self.JOIN_CODE_LENGTH)
            )
            if not await self.__repo.join_code_exists(code):
                return code
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate a unique join code, please retry",
        )

    async def _get_classroom(self, classroom_id: uuid.UUID) -> Classroom:
        classroom = await self.__repo.get_classroom(classroom_id)
        if classroom is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
        return classroom

    def _ensure_owner(self, classroom: Classroom, user: User) -> None:
        if classroom.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the lecturer who owns this classroom can do that",
            )

    async def _ensure_access(
        self, classroom: Classroom, user: User
    ) -> ClassroomMember | None:
        if classroom.owner_id == user.id:
            return None
        membership = await self.__repo.get_membership(classroom.id, user.id)
        if membership is None or not membership.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not an active member of this classroom",
            )
        return membership

    def _classroom_dir(self, classroom_id: uuid.UUID) -> Path:
        return self.__upload_root / str(classroom_id)

    def _materials_dir(self, classroom_id: uuid.UUID) -> Path:
        return self._classroom_dir(classroom_id) / "materials"

    def _assessment_dir(self, classroom_id: uuid.UUID, assessment_id: uuid.UUID) -> Path:
        return self._classroom_dir(classroom_id) / "assessments" / str(assessment_id)

    @staticmethod
    def _default_name(user: User) -> str:
        return f"{user.first_name} {user.last_name}".strip() or user.email

    @staticmethod
    def _original_name(filename: str | None) -> str:
        name = Path(filename or "upload").name
        return name[:255] or "upload"

    @staticmethod
    def _stored_name(filename: str | None) -> str:
        suffix = "".join(c for c in Path(filename or "").suffix.lower() if c.isalnum() or c == ".")
        return f"{uuid.uuid4().hex}{suffix[:16]}"

    async def _save_upload(self, file: UploadFile, destination: Path) -> int:
        max_bytes = setting.max_upload_size_mb * 1024 * 1024
        destination.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        try:
            with destination.open("wb") as buffer:
                while chunk := await file.read(self.CHUNK_SIZE):
                    size += len(chunk)
                    if size > max_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=f"File is larger than the {setting.max_upload_size_mb}MB limit",
                        )
                    buffer.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await file.close()
        return size

    # ------------------------------------------------------------------ classrooms
    async def create_classroom(self, owner: User, data: ClassroomCreate) -> Classroom:
        classroom = Classroom(
            name=data.name,
            join_code=await self._new_join_code(),
            owner_id=owner.id,
        )
        return await self.__repo.add_classroom(classroom)

    async def list_classrooms(self, user: User) -> list[Classroom]:
        if user.role == Role.lecture:
            return await self.__repo.list_classrooms_owned_by(user.id)
        return await self.__repo.list_classrooms_for_student(user.id)

    async def get_classroom(self, user: User, classroom_id: uuid.UUID) -> Classroom:
        classroom = await self._get_classroom(classroom_id)
        await self._ensure_access(classroom, user)
        return classroom

    async def update_classroom(
        self, user: User, classroom_id: uuid.UUID, data: ClassroomUpdate
    ) -> Classroom:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        if data.name is not None:
            classroom.name = data.name
        if data.regenerate_join_code:
            classroom.join_code = await self._new_join_code()
        return await self.__repo.save_classroom(classroom)

    async def delete_classroom(self, user: User, classroom_id: uuid.UUID) -> None:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        await self.__repo.delete_classroom(classroom)
        shutil.rmtree(self._classroom_dir(classroom.id), ignore_errors=True)

    async def join_classroom(self, user: User, data: JoinClassroom) -> ClassroomMember:
        code = data.join_code.strip().upper()
        classroom = await self.__repo.get_classroom_by_join_code(code)
        if classroom is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid class key")
        existing = await self.__repo.get_membership(classroom.id, user.id)
        conflict = await self.__repo.get_member_by_index_number(
            classroom.id, data.index_number
        )
        if conflict is not None and (existing is None or conflict.id != existing.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That index number is already registered in this classroom",
            )
        name = data.name or self._default_name(user)
        if existing is not None:
            if existing.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already joined this classroom",
                )
            existing.is_active = True
            existing.name = name
            existing.index_number = data.index_number
            return await self.__repo.save_member(existing)
        member = ClassroomMember(
            classroom_id=classroom.id,
            student_id=user.id,
            student=user,
            name=name,
            index_number=data.index_number,
        )
        return await self.__repo.add_member(member)

    # ------------------------------------------------------------------ members
    async def list_students(self, user: User, classroom_id: uuid.UUID) -> list[ClassroomMember]:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        return await self.__repo.list_members(classroom.id)

    async def add_student(
        self, user: User, classroom_id: uuid.UUID, data: AddStudent
    ) -> ClassroomMember:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        student = await self.__repo.get_user_by_email(str(data.email))
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account exists with that email",
            )
        if student.role != Role.student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only student accounts can be added to a classroom",
            )
        existing = await self.__repo.get_membership(classroom.id, student.id)
        conflict = await self.__repo.get_member_by_index_number(
            classroom.id, data.index_number
        )
        if conflict is not None and (existing is None or conflict.id != existing.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That index number is already registered in this classroom",
            )
        name = data.name or self._default_name(student)
        if existing is not None:
            if existing.is_active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="That student is already in this classroom",
                )
            existing.is_active = True
            existing.name = name
            existing.index_number = data.index_number
            return await self.__repo.save_member(existing)
        member = ClassroomMember(
            classroom_id=classroom.id,
            student_id=student.id,
            student=student,
            name=name,
            index_number=data.index_number,
        )
        return await self.__repo.add_member(member)

    async def update_student(
        self, user: User, classroom_id: uuid.UUID, student_id: uuid.UUID, data: UpdateStudent
    ) -> ClassroomMember:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        member = await self.__repo.get_membership(classroom.id, student_id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student is not in this classroom"
            )
        updates = data.model_dump(exclude_unset=True)
        for field in ("name", "index_number", "is_active"):
            if updates.get(field) is None:
                updates.pop(field, None)
        if "index_number" in updates and updates["index_number"] != member.index_number:
            conflict = await self.__repo.get_member_by_index_number(
                classroom.id, updates["index_number"]
            )
            if conflict is not None and conflict.id != member.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="That index number is already registered in this classroom",
                )
        for field, value in updates.items():
            setattr(member, field, value)
        return await self.__repo.save_member(member)

    async def remove_student(
        self, user: User, classroom_id: uuid.UUID, student_id: uuid.UUID
    ) -> None:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        member = await self.__repo.get_membership(classroom.id, student_id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Student is not in this classroom"
            )
        await self.__repo.delete_member(member)

    # ------------------------------------------------------------------ materials
    async def upload_material(
        self, user: User, classroom_id: uuid.UUID, file: UploadFile
    ) -> ClassroomMaterial:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="A file is required"
            )
        stored_name = self._stored_name(file.filename)
        destination = self._materials_dir(classroom.id) / stored_name
        size = await self._save_upload(file, destination)
        material = ClassroomMaterial(
            classroom_id=classroom.id,
            uploaded_by_id=user.id,
            original_name=self._original_name(file.filename),
            stored_name=stored_name,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size,
        )
        try:
            return await self.__repo.add_material(material)
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    async def list_materials(self, user: User, classroom_id: uuid.UUID) -> list[ClassroomMaterial]:
        classroom = await self._get_classroom(classroom_id)
        await self._ensure_access(classroom, user)
        return await self.__repo.list_materials(classroom.id)

    async def get_material_for_download(
        self, user: User, material_id: uuid.UUID
    ) -> tuple[ClassroomMaterial, Path]:
        material = await self.__repo.get_material(material_id)
        if material is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
        classroom = await self._get_classroom(material.classroom_id)
        await self._ensure_access(classroom, user)
        path = self._materials_dir(classroom.id) / material.stored_name
        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is missing")
        return material, path

    async def delete_material(self, user: User, material_id: uuid.UUID) -> None:
        material = await self.__repo.get_material(material_id)
        if material is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
        classroom = await self._get_classroom(material.classroom_id)
        self._ensure_owner(classroom, user)
        path = self._materials_dir(classroom.id) / material.stored_name
        await self.__repo.delete_material(material)
        path.unlink(missing_ok=True)

    # ------------------------------------------------------------------ assessments
    async def create_assessment(
        self, user: User, classroom_id: uuid.UUID, data: AssessmentCreate
    ) -> Assessment:
        classroom = await self._get_classroom(classroom_id)
        self._ensure_owner(classroom, user)
        assessment = Assessment(
            classroom_id=classroom.id,
            created_by_id=user.id,
            type=data.type,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
        )
        return await self.__repo.add_assessment(assessment)

    async def list_assessments(self, user: User, classroom_id: uuid.UUID) -> list[Assessment]:
        classroom = await self._get_classroom(classroom_id)
        await self._ensure_access(classroom, user)
        return await self.__repo.list_assessments(classroom.id)

    async def get_assessment(self, user: User, assessment_id: uuid.UUID) -> Assessment:
        assessment = await self.__repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        classroom = await self._get_classroom(assessment.classroom_id)
        await self._ensure_access(classroom, user)
        return assessment

    async def update_assessment(
        self, user: User, assessment_id: uuid.UUID, data: AssessmentUpdate
    ) -> Assessment:
        assessment = await self.__repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        classroom = await self._get_classroom(assessment.classroom_id)
        self._ensure_owner(classroom, user)
        updates = data.model_dump(exclude_unset=True)
        if updates.get("title") is None:
            updates.pop("title", None)
        if updates.get("due_date") is None:
            updates.pop("due_date", None)
        for field, value in updates.items():
            setattr(assessment, field, value)
        return await self.__repo.save_assessment(assessment)

    async def delete_assessment(self, user: User, assessment_id: uuid.UUID) -> None:
        assessment = await self.__repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        classroom = await self._get_classroom(assessment.classroom_id)
        self._ensure_owner(classroom, user)
        await self.__repo.delete_assessment(assessment)
        shutil.rmtree(self._assessment_dir(classroom.id, assessment.id), ignore_errors=True)

    # ------------------------------------------------------------------ submissions
    async def submit_assessment(
        self,
        user: User,
        assessment_id: uuid.UUID,
        file: UploadFile | None,
        text_answer: str | None,
    ) -> Submission:
        assessment = await self.__repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        classroom = await self._get_classroom(assessment.classroom_id)
        membership = await self.__repo.get_membership(classroom.id, user.id)
        if membership is None or not membership.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not an active member of this classroom",
            )
        existing = await self.__repo.get_submission_by_student(assessment.id, user.id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted this assessment",
            )
        if not text_answer and (file is None or not file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide a file, a text answer, or both",
            )

        stored_name: str | None = None
        original_name: str | None = None
        content_type: str | None = None
        size_bytes: int | None = None
        destination: Path | None = None
        if file is not None and file.filename:
            stored_name = self._stored_name(file.filename)
            original_name = self._original_name(file.filename)
            content_type = file.content_type or "application/octet-stream"
            destination = self._assessment_dir(classroom.id, assessment.id) / stored_name
            size_bytes = await self._save_upload(file, destination)

        due_date = assessment.due_date
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=UTC)
        submission = Submission(
            assessment_id=assessment.id,
            student_id=user.id,
            student=user,
            text_answer=text_answer,
            original_name=original_name,
            stored_name=stored_name,
            content_type=content_type,
            size_bytes=size_bytes,
            submitted_at=datetime.now(UTC),
            is_late=datetime.now(UTC) > due_date,
        )
        try:
            return await self.__repo.add_submission(submission)
        except Exception:
            if destination is not None:
                destination.unlink(missing_ok=True)
            raise

    async def list_submissions(self, user: User, assessment_id: uuid.UUID) -> list[Submission]:
        assessment = await self.__repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        classroom = await self._get_classroom(assessment.classroom_id)
        self._ensure_owner(classroom, user)
        return await self.__repo.list_submissions(assessment.id)

    async def get_my_submission(
        self, user: User, assessment_id: uuid.UUID
    ) -> Submission:
        assessment = await self.__repo.get_assessment(assessment_id)
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        classroom = await self._get_classroom(assessment.classroom_id)
        membership = await self.__repo.get_membership(classroom.id, user.id)
        if membership is None or not membership.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not an active member of this classroom",
            )
        submission = await self.__repo.get_submission_by_student(assessment.id, user.id)
        if submission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="You have not submitted this yet"
            )
        return submission

    async def get_submission_for_download(
        self, user: User, submission_id: uuid.UUID
    ) -> tuple[Submission, Path]:
        submission = await self.__repo.get_submission(submission_id)
        if submission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
            )
        assessment = await self.__repo.get_assessment(submission.assessment_id)
        if assessment is None:  # pragma: no cover - FK guarantees it
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
            )
        classroom = await self._get_classroom(assessment.classroom_id)
        if classroom.owner_id != user.id and submission.student_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this submission",
            )
        if not submission.stored_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="This submission has no file"
            )
        path = self._assessment_dir(classroom.id, assessment.id) / submission.stored_name
        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is missing")
        return submission, path
