from datetime import datetime, timedelta, timezone
import jwt

SECRET_KEY = "909d3c71bb0553a5dfad5630f108a6c6044a6d31b906d957cd3000f6186e864f"
ALGORITHM = "HS256"

# 配置OAuth2 Bearer 模式
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

#创建jwt，创建一个令牌。登陆成功后，返回用户信息，生成一个token发给前端
#每次请求都需要在header中携带token，token过期后需要重新登陆
def encode_jwt(payload: dict) -> str:
    payload_copy = payload.copy()
    # 更新过期时间为30分钟后。注意使用 utc 时间
    payload_copy["exp"] = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload_copy["iat"] = datetime.now(timezone.utc)
    # 加密生产 一个 token
    token = jwt.encode(payload_copy, key =SECRET_KEY, algorithm=ALGORITHM)
    return token

# 解码jwt，校验token是否过期或非法
#校验通过后 返回用户信息（payload 不要放敏感信息） 
def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("token已经过期")
    except jwt.InvalidTokenError:
        raise Exception("非法token")
    except Exception as e:
        raise Exception(f"token校验失败: {str(e)}")
