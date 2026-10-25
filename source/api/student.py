from fastapi import APIRouter


router = APIRouter(prefix="/student", tags=["students"])

@router.get("/")
async def student():
    return {"student":"oswald banini"}