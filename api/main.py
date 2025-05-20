"""
FastAPI 应用程序主入口

此模块负责：
1. 创建和配置 FastAPI 应用实例
2. 注册路由器
3. 配置 CORS
4. 提供获取应用实例的工厂函数
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import search, whitelist


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例
    
    配置包括：
    - API 元数据（标题、描述、版本）
    - CORS 中间件
    - 路由器注册
    
    Returns:
        配置好的 FastAPI 应用实例
    """
    # 创建 FastAPI 应用
    app = FastAPI(
        title="同步电报搜索 API",
        description="为 Telegram 中文历史消息搜索提供 API 服务",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        # 允许的源列表（域名），前端开发服务器默认在 5173 端口
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有 HTTP 方法
        allow_headers=["*"],  # 允许所有请求头
    )
    
    # 注册路由器
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(whitelist.router, prefix="/api/v1")
    
    # 注册启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动时执行的事件"""
        logging.getLogger(__name__).info("FastAPI 应用启动")
    
    # 注册关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭时执行的事件"""
        logging.getLogger(__name__).info("FastAPI 应用关闭")
    
    return app


# 应用实例，可以被导入并访问
app = create_app()