from enum import Enum
from pydantic import BaseModel, EmailStr

class Role(str, Enum):
    student = "student",
    lecture = "lecture",
    admin = "admin",
    super_admin = "super_admin"

class User_base(BaseModel):
    first_name: str
    last_name:str
    email: EmailStr

class Register_user_response(User_base):
    role:Role = Role.student

class Register_user(User_base):
    password: str

class Login_response(BaseModel):
    token:str
    type: str = "bearer"
