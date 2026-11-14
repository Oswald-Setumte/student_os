import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from source.core.security import lecturer, protected, student
from source.database.session import get_session
from source.schemas.lecture_schema import (
    AddStudent,
    AssessmentCreate,
    AssessmentResponse,
    AssessmentUpdate,
    ClassroomCreate,
    ClassroomMemberResponse,
    ClassroomResponse,
    ClassroomUpdate,
    JoinClassroom,
    MaterialResponse,
    SubmissionResponse,
    UpdateStudent,
)
from source.services.lecture_services import LectureService

router = APIRouter(prefix="/api/lecture", tags=["lecture"])

DB = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------- classrooms
@router.post("/classrooms", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
async def create_classroom(data: ClassroomCreate, user: lecturer, db: DB):
    return await LectureService(session=db).create_classroom(owner=user, data=data)


@router.get("/classrooms", response_model=list[ClassroomResponse])
async def list_classrooms(user: protected, db: DB):
    return await LectureService(session=db).list_classrooms(user=user)


@router.post("/classrooms/join", response_model=ClassroomMemberResponse)
async def join_classroom(data: JoinClassroom, user: student, db: DB):
    return await LectureService(session=db).join_classroom(user=user, data=data)


@router.get("/classrooms/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(classroom_id: uuid.UUID, user: protected, db: DB):
    return await LectureService(session=db).get_classroom(user=user, classroom_id=classroom_id)


@router.patch("/classrooms/{classroom_id}", response_model=ClassroomResponse)
async def update_classroom(
    classroom_id: uuid.UUID, data: ClassroomUpdate, user: lecturer, db: DB
):
    return await LectureService(session=db).update_classroom(
        user=user, classroom_id=classroom_id, data=data
    )


@router.delete("/classrooms/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_classroom(classroom_id: uuid.UUID, user: lecturer, db: DB):
    await LectureService(session=db).delete_classroom(user=user, classroom_id=classroom_id)


# ---------------------------------------------------------------------- students
@router.get("/classrooms/{classroom_id}/students", response_model=list[ClassroomMemberResponse])
async def list_students(classroom_id: uuid.UUID, user: lecturer, db: DB):
    return await LectureService(session=db).list_students(user=user, classroom_id=classroom_id)


@router.post(
    "/classrooms/{classroom_id}/students",
    response_model=ClassroomMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_student(classroom_id: uuid.UUID, data: AddStudent, user: lecturer, db: DB):
    return await LectureService(session=db).add_student(
        user=user, classroom_id=classroom_id, data=data
    )


@router.patch(
    "/classrooms/{classroom_id}/students/{student_id}",
    response_model=ClassroomMemberResponse,
)
async def update_student(
    classroom_id: uuid.UUID,
    student_id: uuid.UUID,
    data: UpdateStudent,
    user: lecturer,
    db: DB,
):
    return await LectureService(session=db).update_student(
        user=user, classroom_id=classroom_id, student_id=student_id, data=data
    )


@router.delete(
    "/classrooms/{classroom_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_student(classroom_id: uuid.UUID, student_id: uuid.UUID, user: lecturer, db: DB):
    await LectureService(session=db).remove_student(
        user=user, classroom_id=classroom_id, student_id=student_id
    )


# ---------------------------------------------------------------------- materials
@router.post(
    "/classrooms/{classroom_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    classroom_id: uuid.UUID,
    user: lecturer,
    db: DB,
    file: Annotated[UploadFile, File(description="Any file format")],
):
    return await LectureService(session=db).upload_material(
        user=user, classroom_id=classroom_id, file=file
    )


@router.get("/classrooms/{classroom_id}/materials", response_model=list[MaterialResponse])
async def list_materials(classroom_id: uuid.UUID, user: protected, db: DB):
    return await LectureService(session=db).list_materials(
        user=user, classroom_id=classroom_id
    )


@router.get("/materials/{material_id}/download")
async def download_material(material_id: uuid.UUID, user: protected, db: DB):
    material, path = await LectureService(session=db).get_material_for_download(
        user=user, material_id=material_id
    )
    return FileResponse(
        path=path, filename=material.original_name, media_type=material.content_type
    )


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(material_id: uuid.UUID, user: lecturer, db: DB):
    await LectureService(session=db).delete_material(user=user, material_id=material_id)


# ---------------------------------------------------------------------- assessments
@router.post(
    "/classrooms/{classroom_id}/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment(
    classroom_id: uuid.UUID, data: AssessmentCreate, user: lecturer, db: DB
):
    return await LectureService(session=db).create_assessment(
        user=user, classroom_id=classroom_id, data=data
    )


@router.get(
    "/classrooms/{classroom_id}/assessments", response_model=list[AssessmentResponse]
)
async def list_assessments(classroom_id: uuid.UUID, user: protected, db: DB):
    return await LectureService(session=db).list_assessments(
        user=user, classroom_id=classroom_id
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: uuid.UUID, user: protected, db: DB):
    return await LectureService(session=db).get_assessment(
        user=user, assessment_id=assessment_id
    )


@router.patch("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: uuid.UUID, data: AssessmentUpdate, user: lecturer, db: DB
):
    return await LectureService(session=db).update_assessment(
        user=user, assessment_id=assessment_id, data=data
    )


@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(assessment_id: uuid.UUID, user: lecturer, db: DB):
    await LectureService(session=db).delete_assessment(
        user=user, assessment_id=assessment_id
    )


# ---------------------------------------------------------------------- submissions
@router.post(
    "/assessments/{assessment_id}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assessment(
    assessment_id: uuid.UUID,
    user: student,
    db: DB,
    file: Annotated[UploadFile | None, File(description="Any file format")] = None,
    text_answer: Annotated[str | None, Form()] = None,
):
    return await LectureService(session=db).submit_assessment(
        user=user, assessment_id=assessment_id, file=file, text_answer=text_answer
    )


@router.get(
    "/assessments/{assessment_id}/submissions",
    response_model=list[SubmissionResponse],
)
async def list_submissions(assessment_id: uuid.UUID, user: lecturer, db: DB):
    return await LectureService(session=db).list_submissions(
        user=user, assessment_id=assessment_id
    )


@router.get(
    "/assessments/{assessment_id}/submission",
    response_model=SubmissionResponse,
)
async def get_my_submission(assessment_id: uuid.UUID, user: student, db: DB):
    return await LectureService(session=db).get_my_submission(
        user=user, assessment_id=assessment_id
    )


@router.get("/submissions/{submission_id}/download")
async def download_submission(submission_id: uuid.UUID, user: protected, db: DB):
    submission, path = await LectureService(session=db).get_submission_for_download(
        user=user, submission_id=submission_id
    )
    return FileResponse(
        path=path,
        filename=submission.original_name or "submission",
        media_type=submission.content_type or "application/octet-stream",
    )
