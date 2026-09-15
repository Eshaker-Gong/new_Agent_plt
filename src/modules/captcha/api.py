from redis.asyncio.client import Redis
from src.infra.redis_cache import get_redis_client
from src.modules.captcha.schema import CaptchaRead
from fastapi import APIRouter, Depends
from src.core.base_schema import ResponseSchema
from src.modules.captcha.service import CaptchaService

router = APIRouter(prefix="/captcha",tags=["验证码"])

#注入CaptchaService依赖、 CaptchService 依赖 Redis 
def get_captcha_service(redis: Redis = Depends(get_redis_client)) -> CaptchaRead:
    return CaptchaService(redis=redis)

# GET /api/v1/captcha     获取验证码
@router.get("",response_model=ResponseSchema[CaptchaRead],summary="获取验证码")
async def get_capture(
    svc:CaptchaService = Depends(get_captcha_service),
):
    captcha = await svc.create_captcha()
    return ResponseSchema[CaptchaRead](data=captcha)
    


#POST /api/v1/captcha/verify     校验验证码