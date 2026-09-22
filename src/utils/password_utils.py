import bcrypt
#同一个字符串，每次加密都不一样，防止彩虹表攻击
#md5 是 每次加密都一样，不能防止彩虹表攻击
#bcrypt 是 哈希加密，不能彩虹表攻击，但是计算量大，速度慢

def hash_password(plain_password: str) -> str:
    """明文密码 → bcrypt 哈希"""
    return bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码是否匹配哈希"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )