from redis.asyncio import Redis
from src.modules.user.repository import UserRepository
from src.core.exceptions import BizException
from src.modules.captcha.schema import CaptchaVerifyRequest
from src.modules.captcha.service import CaptchaService
from src.modules.auth.schema import TokenResponse
from src.modules.auth.schema import LoginRequest
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.password_utils import verify_password
from src.utils.jwt_utils import encode_jwt
from datetime import datetime




class AuthService():
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.captcha_service = CaptchaService(redis)
        self.user_repo = UserRepository(self.db)

    async def login(self, data: LoginRequest) -> TokenResponse:
        # 1. 校验验证码
        captcha_verify_req = CaptchaVerifyRequest(
            captcha_key=data.captcha_key,
            captcha_code=data.captcha_code,
        )
        await self.captcha_service.verify_captcha(captcha_verify_req)
        
        # 2.校验通过。查询用户信息
        user = await self.user_repo.get_by_username(data.username)
        if not user:
            raise BizException(code=10002,message="用户不存在")
        if not user.is_active:
            raise BizException(code=10004,message="用户已被禁用")
        
        # 3.校验通过。校验密码
        if not verify_password(data.password, user.hash_password):
            raise BizException(code=10003,message="密码错误")
        
        # 4.校验通过。登录成功。生成token
        payload = {"sub": user.id, "username": user.username, "email": user.email}
        token = encode_jwt(payload)

        # 5。修改登录时间
        user.last_login_time = datetime.now()
        await self.user_repo.update(user)

        return TokenResponse(access_token=token)
