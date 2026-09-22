from redis.asyncio.client import Redis
from src.modules.captcha.schema import CaptchaRead,CaptchaVerifyRequest
import random
import string
import uuid
import base64
from captcha.image import ImageCaptcha
from src.core.exceptions import BizException

# 定义验证码字符集
captcha_chars = string.ascii_letters + string.digits

class CaptchaService():
    #验证码过期时间，单位秒
    CAPTCHA_EXPIRE = 60 * 5
    #验证码前缀
    CAPTCHA_KEY_EXPIRE = "captcha:"

    def __init__(self, redis: Redis):
        self.redis = redis

    def random_code(self) -> str:
        """生成随机验证码"""
        code = "".join(random.choices(string.ascii_letters + string.digits, k=4))
        #去除混淆字符
        code = code.replace("0", "O").replace("1", "I").replace("l", "L")
        return code 
    
    #创建验证码
    async def create_captcha(self) -> CaptchaRead:
        #1.得到四位随机验证码 真正值
        code = self.random_code()
        #2.生产验证码的唯一ID
        captcha_id = str(uuid.uuid4())
        #3.生成验证码键
        key = f"{self.CAPTCHA_KEY_EXPIRE}{captcha_id}"
        #4.将验证码存储到Redis中
        await self.redis.set(key, code, ex=self.CAPTCHA_EXPIRE)

        # 以上为服务端 保存验证码 到 Redis 中

        # 5.生成验证码图片，编码为base64字符串
        image_captcha = ImageCaptcha(width=162, height=54)
        image_data = image_captcha.generate(code)
        b64 = base64.b64encode(image_data.read()).decode()

        # 6.返回验证码图片
        return CaptchaRead(
            key = captcha_id,
            image = f"data:image/png;base64,{b64}"
            )



    #校验验证码
    async def verify_captcha(self, captcha: CaptchaVerifyRequest) -> bool:
        #1.从Redis中获取验证码
        key = f"{self.CAPTCHA_KEY_EXPIRE}{captcha.key}"
        #2.从Redis中获取数据
        code = await self.redis.get(key)
        if not code:
            raise BizException(code= "10001",message="验证码不存在或过期")
        if code.lower() != captcha.code.lower():
            raise BizException(code= "10002",message="验证码错误")
        #3.删除验证码
        await self.redis.delete(key)

        #4.校验通过
        return True
