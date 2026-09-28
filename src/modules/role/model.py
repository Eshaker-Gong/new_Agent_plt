from src.modules.permission.model import Permission
from sqlalchemy.orm import relationship
from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy import Table, Column, BigInteger, ForeignKey
from src.core.base_model import Base, BaseModel



# 角色权限关联表--中间表：联合主键/复合主键 防重复效果
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

# 角色模型  role.permissions 可以拿到角色的所有权限
class Role(BaseModel):
    __tablename__ = "roles"
    code: Mapped[str] = mapped_column(String(100), unique=True, comment="角色编码")
    name: Mapped[str] = mapped_column(String(100),  comment="角色名称")
    description: Mapped[str] = mapped_column(String(200), nullable=True, comment="角色描述")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        lazy="selectin",
        # backref="roles", 
    )

# 用户角色关联表--中间表：联合主键/复合主键 防重复效果
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)