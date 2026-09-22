# 02 · 功能要点、难点与设计方法论

> 从「这个功能解决什么 → 技术要点 → 难点/坑 → 为什么这么做（方法论）」四个维度拆解。

---

## 1. 统一配置管理（core/config.py）

- **解决什么**：数据库/Redis 地址、密码、日志级别等环境差异不能写死在代码里。
- **技术要点**：
  - `pydantic-settings.BaseSettings` 自动从 `.env` 和环境变量读取，并做类型转换（`DB_PORT: int`、`APP_DEBUG: bool`）。
  - `DATABASE_URL` 用 `@property` 拼接 `mysql+asyncmy://...?charset=utf8mb4`，asyncmy 是异步驱动。
  - `@lru_cache` 装饰 `get_settings()`，全局只读一次，本质是**手写单例**。
- **难点/坑**：
  - 必须用异步驱动（`asyncmy`）才能配合 `AsyncEngine`，装成 `pymysql` 会在异步上下文报错。
  - lru_cache 在测试切换环境变量时不会刷新（测试时是需要留意的点）。
- **方法论**：配置与代码分离（12-Factor App 第 3 条）；单一可信来源（Single Source of Truth）；不可变单例。

---

## 2. 异步数据库与会话事务（infra/database.py）

- **解决什么**：高并发 I/O 场景下避免同步 DB 调用阻塞事件循环；保证请求级事务正确提交/回滚。
- **技术要点**：
  - `create_async_engine` + 连接池参数：`pool_size=10 / max_overflow=20 / pool_recycle=3600 / pool_pre_ping=True`。
  - `async_sessionmaker(..., expire_on_commit=False)`：提交后对象属性仍可用，避免异步惰性加载触发异常。
  - `get_db()` 用生成器依赖：`yield session` → 成功 `commit`，异常 `rollback`。
- **难点/坑**：
  - `pool_pre_ping`：MySQL 默认 8 小时空闲断连，pre_ping 取连接前先探活，避免拿到“死连接”。
  - `pool_recycle=3600` 主动回收，比 8 小时更保守。
  - **异步里最常见的坑：lazy load**。commit 后再访问未加载关系会触发同步 IO 报错，`expire_on_commit=False` + 显式 `selectinload/await` 是正解。
  - Repository 用 `flush` 而不是 `commit`：把提交权上交给请求级 `get_db`，保证一个请求内多个写操作在同一事务里。
- **方法论**：
  - **事务边界放在最外层（请求作用域）**，Service/Repository 只 flush 不 commit，分层清晰、可组合。
  - 连接池是昂贵资源，应用级单例、请求级 session。

---

## 3. ORM 基类与通用仓储（base_model.py / base_repository.py）

- **解决什么**：每张表都要 id/时间戳，每个仓储都要增删改查，避免重复。
- **技术要点**：
  - `DeclarativeBase` + `TimestampMixin`（`server_default=func.now()`、`onupdate=func.now()`）。
  - 时间由**数据库**维护而非 Python，多实例部署时时间口径一致。
  - `BaseRepository(Generic[T])` + `TypeVar("T", bound=BaseModel)`：类型安全的泛型 CRUD，`UserRepository(BaseRepository[User])` 自动获得类型提示。
  - `get_all` 内置 `offset/limit` 分页。
- **难点/坑**：
  - `BigInteger` 主键：为未来分表/雪花 ID 预留空间，避免 int 溢出。
  - 泛型 `bound` 约束让 T 只能是 BaseModel 子类，既复用又不丢失类型。
- **方法论**：DRY + 泛型/模板复用；约定优于配置（所有表统一审计字段）。

---

## 4. 统一响应与全局异常（base_schema.py / exceptions.py）

- **技术要点**：
  - `ResponseSchema[T]`（code/message/data）+ FastAPI `response_model` 泛型，前端拿到结构永远一致。
  - 自定义 `BizException(code, message)`，业务规则失败直接 raise。
  - 注册两个 handler：业务异常 → HTTP 200 + 业务码（`code=400/404`）；兜底 `Exception` → 500 并 `logger.exception` 打堆栈。
- **难点/坑 / 可讨论点**：
  - 业务异常返回 HTTP 200 是一种常见（但有争议）的选择；REST 纯粹派会主张返回 4xx。面试中应能说出两种风格的权衡。
  - 必须有兜底 handler，否则未捕获异常会泄漏堆栈/SQL 给前端。
- **方法论**：失败也要有契约（统一错误结构）；错误信息对外友好、对内详细（日志记真异常）。

---

## 5. 日志体系（logger.py + middlewares/logging.py）

- **技术要点**：
  - loguru 双通道：控制台彩色（开发）+ 文件（按天 `rotation="00:00"`、保留 30 天、`gz` 压缩）。
  - 中间件记录 `方法 路径 状态码 耗时ms`，用 `time.perf_counter()` 高精度计时。
  - 在 `lifespan` 启动时初始化，配置随环境变量走。
- **难点/坑**：
  - `logger.remove()` 先移除默认 handler，避免重复输出。
  - 文件日志必须轮转+压缩+保留期，否则磁盘会被写爆（生产事故常见点）。
- **方法论**：可观测性三支柱中的“日志”；请求级耗时是定位慢接口/做性能基线的最小成本手段。

---

## 6. 应用生命周期（main.py lifespan）

- **技术要点**：`@asynccontextmanager lifespan` 在启动时初始化日志，在关闭时 `await engine.dispose()` 释放连接池。
- **方法论**：优雅启停（graceful startup/shutdown），资源“谁创建谁释放”，避免连接泄漏。

---

## 7. 用户模块（modules/user，五件套）

- **要点**：完整演示分层闭环。
  - Model：`username/email` 唯一索引、`is_active/is_superuser/last_login_at`。
  - Schema：`UserCreate`（入参，`EmailStr` 校验）、`UserRead`（出参，`from_attributes=True` 从 ORM 转换）。
  - Repository：在通用 CRUD 上扩展 `get_by_username/get_by_email`。
  - Service：唯一性校验，冲突抛 `BizException`。
  - API：`POST /users`、`GET /users/{id}`、`GET /users`，全部包统一响应体。
- **难点/坑**：
  - **出参绝不返回 `hashed_password`**：靠 `UserRead` 白名单字段从源头杜绝，而不是“记得别返回”。
  - 唯一性靠应用层先查 + DB 唯一索引双保险（高并发下先查可能漏，唯一索引兜底）。
- **方法论**：读写模型分离（CQRS-lite 的入参/出参 DTO）；纵深防御（应用校验 + 数据库约束）。

---

## 8. 图形验证码（modules/captcha，最新功能）

- **解决什么**：登录/敏感操作防机器人、防暴力破解、防接口重放。
- **技术要点**：
  - 生成 4 位随机码 → `uuid4` 作为 key → 存 Redis（`captcha:{uuid}`，`ex=300s` 自动过期）。
  - `captcha.image.ImageCaptcha` 生成图片 → base64 → `data:image/png;base64,...` 内联返回，前端无需多一次静态请求。
  - 校验：取值 → 不存在/过期报错（码 10001）→ 大小写不敏感比较（10002）→ **通过后立即删除（一次性）**。
  - Service 通过 `Depends(get_redis_client)` 注入，无状态、可水平扩展。
- **难点/坑**：
  - **为什么存 Redis 而不是内存/JWT**：多实例部署时内存不共享；验证码必须服务端可控、可过期、可删除。
  - **一次性使用（delete after verify）**：防止同一个验证码被重放刷接口。
  - **去除易混淆字符**（0/O、1/I/l）降低人工识别失败率。
  - 大小写不敏感比较提升体验，同时不降低安全性（验证码本就短时效）。
  - TTL 是安全关键：5 分钟把暴力破解窗口压到最小。
- **方法论**：
  - 无状态服务 + 有状态外置存储（Redis）= 水平扩展能力。
  - 安全设计三原则：短时效、一次性、服务端持有真值（客户端只拿不可读的图片）。
  - 用 `key`（uuid）而不是自增 id，避免验证码被枚举/遍历。

---

## 9. 认证模块（modules/auth + utils，进行中）

- **已就位的能力**：
  - `jwt_utils`：HS256 签发，payload 注入 `exp(30min)/iat`，`OAuth2PasswordBearer(tokenUrl=...)`。
  - `password_utils`：`bcrypt.gensalt()` 加盐哈希 + `checkpw` 校验。
- **待完成**：`/auth/login`（校验账号密码→校验验证码→更新 last_login_at→签发 JWT）、登录态依赖 `get_current_user`、`auth/schema.py` 目前只有注释样例。
- **难点/方法论（面试可主动讲）**：
  - 为什么 bcrypt 而不是 MD5/SHA：随机 salt 使每次哈希不同，抗彩虹表；可调 cost 因子对抗算力提升，代价是慢——而“慢”正是密码哈希想要的。
  - JWT payload 不能放敏感信息（仅 Base64 编码，非加密）。
  - 30 分钟短有效期，配合刷新令牌/登出黑名单（Redis）是常见演进方向。

---

## 10. 数据库迁移（Alembic，异步）

- **要点**：`env.py` 复用项目 `Settings.DATABASE_URL` 与 `Base.metadata`，并用 `async_engine_from_config + asyncio.run` 支持异步驱动；版本链清晰：`init(空) → 建 users → 加 is_superuser`。
- **方法论**：Schema 即版本，迁移脚本可 upgrade/downgrade、可 code review、可随发布流水线执行，杜绝手工改表。

---

## 横切的工程方法论总结（面试一句话版）

1. **分层 + 按领域模块化**：高内聚低耦合，新增业务复制五件套。
2. **配置/代码分离，资源单例、请求级作用域**。
3. **泛型基类收敛重复，差异下沉到子类**。
4. **统一契约（响应/异常/日志）**，让协作方有稳定预期。
5. **事务边界在最外层，存储真值在服务端**（DB 约束、Redis 验证码）。
6. **安全默认值**：密码 bcrypt、JWT 短时效、验证码一次性、出参白名单。
7. **一切状态外置 + 服务无状态**，天然支持水平扩展。
