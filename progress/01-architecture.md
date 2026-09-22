# 01 · 架构与目录结构分析

## 1. 分层架构总览

项目采用经典的 **四层分层 + 按领域模块化（module）** 结构，是 FastAPI 中大型项目的主流做法：

```
                 ┌─────────────────────────────┐
   HTTP 请求 →   │  API 层 (router / endpoint)  │  参数校验、依赖注入、组装响应
                 ├─────────────────────────────┤
                 │  Service 层 (业务编排)        │  业务规则、事务边界、抛业务异常
                 ├─────────────────────────────┤
                 │  Repository 层 (数据访问)     │  只做 CRUD / 查询，不含业务
                 ├─────────────────────────────┤
                 │  Model 层 (SQLAlchemy ORM)   │  表结构映射
                 └─────────────────────────────┘
            横切：core(配置/基类/异常/日志) infra(DB/Redis) middlewares utils
```

依赖方向单向向下：`api → service → repository → model`，上层依赖下层，下层不反向依赖上层。

## 2. 目录结构与职责

```
new_Agent_plt/
├── docker/
│   └── docker-compose.yaml      # MySQL8.4 + Redis + MinIO 三组件一键起
├── alembic/                     # 数据库版本迁移
│   ├── env.py                   # 异步迁移入口，读取项目 Settings 与 Base.metadata
│   └── versions/                # 3 个版本：init → 建 users 表 → 加超管字段
├── src/
│   ├── main.py                  # 应用工厂 create_app + lifespan 生命周期
│   ├── core/                    # 与业务无关的“内核”
│   │   ├── config.py            # 配置项 + lru_cache 单例
│   │   ├── base_model.py        # DeclarativeBase + 时间戳 Mixin + 主键基类
│   │   ├── base_schema.py       # 统一响应体 ResponseSchema[T]（泛型）
│   │   ├── base_repository.py   # 泛型 BaseRepository[T] 通用 CRUD
│   │   ├── exceptions.py        # BizException + 全局异常处理器注册
│   │   └── logger.py            # loguru 控制台/文件双通道 + 轮转
│   ├── infra/                   # 基础设施适配器
│   │   ├── database.py          # 异步引擎、连接池、sessionmaker、get_db 事务依赖
│   │   └── redis_cache.py       # 模块级连接池 + get_redis_client 依赖
│   ├── middlewares/
│   │   └── logging.py           # 请求进出 + 耗时日志中间件
│   ├── utils/
│   │   ├── jwt_utils.py         # JWT 编解码、OAuth2PasswordBearer
│   │   └── password_utils.py    # bcrypt 哈希/校验
│   └── modules/                 # 按业务领域划分
│       ├── user/                #    api/service/repository/model/schema 五件套
│       ├── captcha/             #    api/service/schema（无 DB，用 Redis）
│       └── auth/                #    脚手架（登录进行中）
└── test/                        # pytest（当前仅示例用例）
```

## 3. 关键架构决策（为什么这么分）

- **为什么按 module 切而不是按文件类型切？**
  用户、验证码、认证是不同的限界上下文（Bounded Context）。把同一领域的 5 个文件放一起，
  新增「Agent 管理」「知识库」等模块时直接复制五件套即可，团队协作冲突少、内聚高。

- **为什么要有 core 的 Base 三件套（Model/Repository/Schema）？**
  主键 `id`、`created_at`、`updated_at`、通用 CRUD、统一返回结构是每个领域都会重复的东西。
  用泛型基类 + Mixin 收敛重复代码，新模块只写“差异部分”。这是 **模板方法 / 泛型复用** 思想。

- **为什么区分 infra 与 core？**
  `core` 是抽象/通用能力，`infra` 是具体中间件适配（MySQL、Redis）。
  这对应依赖倒置与六边形架构的雏形——业务不直接写死连接，未来换库/加多数据源时改动收敛在 infra。

- **为什么用依赖注入（Depends）串联？**
  `get_db` 注入会话、`get_redis_client` 注入 Redis、`get_user_service` 注入 Service。
  好处：生命周期由框架管理（请求结束自动关 session/提交回滚）、易于在测试中替换为 mock、
  Service/Repository 不持有全局状态。

## 4. 请求生命周期（以“创建用户”为例）

1. uvicorn 收到 `POST /api/v1/users`
2. `LoggingMiddleware` 记录进入日志、开始计时
3. FastAPI 解析 body → Pydantic `UserCreate`（含 `EmailStr` 邮箱校验）
4. `Depends(get_db)` 打开 AsyncSession；`Depends(get_user_service)` 构造 Service+Repository
5. Service 校验用户名/邮箱唯一 → 不通过抛 `BizException`
6. Repository `create` → `flush + refresh`
7. 正常返回：`get_db` 提交事务；异常：回滚并由全局异常处理器转成统一 JSON
8. `response_model=ResponseSchema[UserRead]` 过滤敏感字段（密码不外露）
9. 中间件记录状态码与耗时
