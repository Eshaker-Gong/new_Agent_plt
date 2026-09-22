# 04 · 面试官视角：亮点、风险与问答清单

> 目的：站在面试官角度评估这个项目，并帮你把“为什么这么做”讲清楚，同时提前准备追问与短板的应对。

## 一、这个项目能证明的能力（加分项）
- 掌握 FastAPI 现代异步写法（`async/await`、依赖注入、`response_model`、lifespan）。
- 有清晰的**分层与模块化架构意识**，不是把所有逻辑堆在一个文件。
- 熟练 SQLAlchemy 2.0 新式声明（`Mapped/mapped_column`）、异步引擎、连接池调优、事务边界设计。
- 理解工程化：配置分离、统一响应/异常/日志、Alembic 迁移、Docker Compose 编排。
- 有安全意识雏形：bcrypt、JWT、验证码一次性 + TTL、出参字段白名单。
- 会用泛型基类做复用（`BaseRepository[T]`、`ResponseSchema[T]`），体现抽象能力。

## 二、面试官大概率会追问的问题（含答题要点）

**Q1：为什么全异步？异步一定更快吗？**
- 异步提升的是**并发吞吐**（I/O 等待时让出事件循环），不是单次延迟；适合 DB/Redis/HTTP 这类 I/O 密集场景。
- CPU 密集任务异步无收益，需要线程/进程池。全链路要避免任何阻塞调用（如同步 pymysql、time.sleep）。

**Q2：事务是怎么管理的？为什么 Repository 只 flush 不 commit？**
- `get_db` 在请求最外层统一 commit/rollback；service 内多次写要么全成功要么全回滚。
- flush 只是把变更发到 DB 拿 ID/校验约束，尚未提交；提交权收敛到边界，保证原子性。

**Q3：`expire_on_commit=False` 解决什么问题？**
- 默认提交后属性过期，异步下再访问会触发隐式惰性加载 → 同步 IO 报错。关闭后提交仍可用属性；需要关系时显式 `selectinload`。

**Q4：连接池参数怎么定的？`pool_pre_ping` 为什么要开？**
- pool_size=10、max_overflow=20 应对突发；pool_recycle=3600 + pre_ping 防止拿到被 MySQL/中间件断开的死连接。具体数值应压测、按实例数与 DB `max_connections` 反推。

**Q5：验证码为什么放 Redis？为什么校验完就删？**
- 服务无状态、多实例共享；Redis 天然 TTL 过期。校验后删除保证一次性，防重放；uuid 作 key 防枚举；短 TTL 压缩暴力窗口。

**Q6：bcrypt 和 MD5 区别？为什么“慢”反而是优点？**
- MD5 快且无盐，易彩虹表/碰撞；bcrypt 随机 salt、每次结果不同、cost 可调，故意提高单次成本，让批量破解代价极高。

**Q7：JWT 被盗怎么办？**
- 短有效期（已做 30min）+ HTTPS；敏感动作二次校验；可加刷新令牌、服务端 Redis 黑名单/版本号实现登出与失效。注意 JWT 默认无法主动撤销。

**Q8：怎么保证用户名/邮箱唯一？高并发下先查后插可靠吗？**
- 不可靠，两个并发请求可能都查不到。靠 DB 唯一索引兜底，捕获 `IntegrityError` 转成业务异常；应用层先查是为了返回友好提示。

**Q9：怎么扩展/测试？**
- 新业务复制 module 五件套；依赖注入使 DB/Redis 可在测试中替换为 SQLite/mock/fakeredis；用 httpx.AsyncClient 做接口测试。

## 三、当前代码里的风险点（面试官可能现场指出，需主动承认并给方案）

> 能主动说出“这里我知道有问题、打算这么改”比被问出来更得分。

1. **JWT 密钥硬编码在 `src/utils/jwt_utils.py`**：应挪到 `.env`/密钥管理；且该密钥已入库视为泄露，需轮换。
2. **建用户密码没有真正哈希**：`user/service.py` 直接把 `data.password` 赋给 `hashed_password`（代码注释也标了 TODO）。上线前必须接 `hash_password`。
3. **`requirements.txt` 与代码不一致**：验证码用了 `captcha`、JWT 用了 `PyJWT`、密码用了 `bcrypt`，但依赖清单里未见对应包 → 新环境 `pip install` 后起不来。需补依赖并锁定版本。
4. **把容器数据卷和密钥提交进了 Git**：`docker/mysql/data`、`docker/minio_data`、`docker/redis_data`、`.env` 被跟踪。应加入 `.gitignore` 并从历史中移除（数据膨胀 + 安全）。
5. **业务异常 HTTP 状态码统一返回 200**：与 REST 语义有冲突，需说明这是团队约定（body 内 code 区分），并能讲清两种风格权衡。
6. **验证码 `BizException(code="10001")` 类型不一致**：其它地方 code 是 int，这里传 str，且 `ResponseSchema.code: int`，可能序列化/类型混乱。应统一为 int 或改字段类型。
7. **`captcha/api.py` 的 `get_captcha_service` 返回类型标注写成了 `CaptchaRead`**（实际返回 `CaptchaService`），是复制粘贴笔误，应修正。
8. **异常处理用裸 `Exception`**：`verify_jwt` 抛 `Exception("token过期")` 过于宽泛，应定义 `TokenExpired/InvalidToken` 等自定义异常并映射 401。
9. **auth 模块未完成**：`api.py` 有 router 但 main 未注册、无登录端点；`schema.py` 只有注释。面试时如实说明这是“进行中”，并讲清下一步实现。
10. **测试仅示例**：`test_sample.py` 甚至含一个故意失败断言；缺少业务/接口测试与 CI。
11. **Redis/DB 模块在 import 期就读 settings 并建池**：不利于测试与多环境，可改为 lifespan 中初始化、app.state 挂载。
12. **`last_login_at` 模型字段存在但建表迁移未包含**（建表迁移无该列，后续也未见补列迁移）→ 模型与迁移不一致，登录写入时会报列不存在，需补迁移。

## 四、简历/自述话术（30 秒电梯版）
“我独立设计了一个 FastAPI 异步后端骨架，面向企业内部 Agent 平台。采用分层 + 按领域模块化结构，
用 SQLAlchemy 2.0 异步和连接池做数据层、Alembic 管理迁移、Redis 支撑图形验证码等安全能力，
并统一了配置、响应、异常与日志规范。已完成用户模块和验证码模块，正在做 JWT 登录鉴权。
过程中我重点处理了异步事务边界、连接保活、验证码一次性防重放和敏感字段不外泄等问题。”

## 五、可延伸的加分方向（被问“下一步怎么演进”时答）
- 鉴权完善：刷新令牌、RBAC 权限（`is_superuser` 已有伏笔）、接口级依赖鉴权。
- 可观测性：接入 Sentry（依赖已在）、结构化日志/traceId 贯穿请求、Prometheus 指标。
- 数据层：多数据源/读写分离、Redis 分布式锁、限流（登录防爆破）。
- 工程质量：Dockerfile + 多阶段构建、CI 跑测试与迁移检查、pre-commit、ruff/mypy。
- 结合“Agent 平台”定位：工具调用鉴权、多租户隔离、Token 配额与审计日志。
