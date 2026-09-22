# {
#   "username": "testuser",
#   "password": "123456",
#   "captcha_key": "550e8400-e29b-41d4-a716-446655440000",
#   "captcha_code": "A3BX"
# }

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_key: str
    captcha_code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"