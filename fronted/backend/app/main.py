from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.redis import close_redis
from app.api import tasks, websocket
from app.tasks.task_processor import start_task_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("Starting PPTAgent Backend Server...")
    await start_task_worker()
    yield
    # 关闭时
    print("Shutting down...")
    await close_redis()


app = FastAPI(
    title="PPTAgent API",
    description="AI Task Management Platform Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tasks.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "PPTAgent API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
