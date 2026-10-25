from enum import Enum
from pydantic import BaseModel, EmailStr

class Role(str, Enum):
    student = "student",
    lecture = "lecture",
    admin = "admin",
    super_admin = "super_admin"

class Register_user_response(BaseModel):
    first_name: str
    last_name:str
    email: EmailStr
    role:Role = Role.student

class Register_user(Register_user_response):
    password: str

class Login_response(BaseModel):
    token:str
    type: str = "baerer"
