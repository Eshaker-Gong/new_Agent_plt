from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    # 从ORM模型中读取属性,需要设置from_attributes=True,
    model_config = {"from_attributes": True}