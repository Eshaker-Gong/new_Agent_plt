from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import get_settings

# 数据库连接池
settings = get_settings()

# 异步数据库引擎创建
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,  # 调试模式，打印SQL语句
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# 异步数据库会话工程创建
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # 提交后会话不会过期
)

# 异步数据库会话获取
async def get_db() -> AsyncSession:
    """FastAPI Depends 注入, 自动提交和异常回滚"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise