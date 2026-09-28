from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import get_db
from src.core.exceptions import BizException
from src.utils.jwt_utils import verify_jwt, oauth2_scheme
from src.modules.user.model import User
#oauth2_scheme 是 fastapi 自带的功能，从Authorization头中提取bearer开头的token
#以后前端发生请求
#GET xxx
#Authorization: Bearer <token>

#根据token 的用户id  查询用户信息，返回用户对象
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT token 中解析当前登录用户，用于保护接口"""
    try:
        payload = verify_jwt(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise BizException(code=401, message="未登录或 token 已过期")

    user = await db.get(User, user_id)
    if not user:
        raise BizException(code=401, message="用户不存在")
    if not user.is_active:
        raise BizException(code=401, message="账号已被禁用")

    return user