from typing import TypeVar, Generic, Type, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.base_model import BaseModel

# 泛型类型声明，bound=BaseModel 表示 T 必须是 BaseModel 的子类或 BaseModel 本身
T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    # 初始化时需要传入模型类和数据库会话（构造函数）
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> T | None:
        return await self.db.get(self.model, id)

    async def get_all(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: T) -> T:
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        await self.db.delete(obj)
        await self.db.flush()