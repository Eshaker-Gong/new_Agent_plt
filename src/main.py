from fastapi import FastAPI
from src.core.config import get_settings
from src.core.logger import setup_logger
from src.core.exceptions import register_exception_handlers
from src.middlewares.logging import LoggingMiddleware
from src.infra.database import engine
from loguru import logger
from src.modules.user.api import router as user_router
from src.modules.captcha.api import router as captcha_router
from src.modules.auth.api import router as auth_router
from src.modules.permission.api import router as permission_router
from src.modules.role.api import router as role_router



# 使用上下文管理器 感知 项目的周期
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()#配置日志组件
    settings = get_settings()
    logger.info(f"应用名称: {settings.APP_NAME} 启动 环境: {settings.APP_ENV}")
    # 应用启动时执行
    yield
    # 应用关闭时执行
    # 关闭数据库连接
    await engine.dispose()
    logger.info(f"{settings.APP_NAME} 已关闭")


# 创建app
def create_app() -> FastAPI:
    settings = get_settings()
    # 创建app应用
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        debug=settings.APP_DEBUG,
        )
    #注册日志中间件
    app.add_middleware(LoggingMiddleware)
    #注册异常处理中间件
    register_exception_handlers(app)
    #注册路由
    app.include_router(user_router, prefix="/api/v1") # 用户路由
    app.include_router(captcha_router, prefix="/api/v1") # 验证码路由
    app.include_router(auth_router, prefix="/api/v1") # 认证路由
    app.include_router(permission_router, prefix="/api/v1") # 权限路由
    app.include_router(role_router, prefix="/api/v1") # 角色路由
    
    return app

# 创建fastapi应用
app = create_app()
@app.get("/health")
async def root():
    return {"status": "ok"}

