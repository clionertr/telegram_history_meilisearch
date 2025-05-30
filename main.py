#!/usr/bin/env python3
"""
主程序入口模块

此模块是整个应用的统一入口点，负责：
1. 配置日志记录
2. 异步启动和管理UserBot和SearchBot两个Telethon客户端
3. 处理信号和键盘中断，确保两个客户端能够优雅地关闭
"""

import asyncio
import logging
import signal
import sys
import uvicorn
from typing import Optional, List, Dict, Any

from user_bot.client import UserBotClient
from search_bot.bot import SearchBot
from api.main import app as fastapi_app

# 全局变量，存储客户端实例，用于在程序退出时确保它们被断开连接
user_bot_client: Optional[UserBotClient] = None
search_bot: Optional[SearchBot] = None
# 存储任务对象，用于在需要时取消任务
tasks: Dict[str, asyncio.Task] = {}
# FastAPI 服务器实例
fastapi_server: Optional[uvicorn.Server] = None
# User Bot 重启事件
userbot_restart_event: asyncio.Event = asyncio.Event()

def setup_logging(level=logging.INFO) -> None:
    """
    配置全局日志记录

    设置统一的日志格式和级别，用于所有模块共享
    
    Args:
        level: 日志级别，默认为INFO
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # 输出到控制台
            # 如果需要，可以添加FileHandler输出到文件
            # logging.FileHandler("sync_all.log")
        ]
    )
    
    # 获取根日志记录器并设置级别
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Telethon的日志可能过于详细，可以调高其级别
    logging.getLogger('telethon').setLevel(logging.WARNING)
    
    logger.info("日志系统初始化完成")

async def shutdown_clients() -> None:
    """
    关闭所有客户端连接
    
    确保所有Telegram客户端优雅地断开连接
    """
    logger = logging.getLogger(__name__)
    
    # 取消所有正在运行的任务
    for name, task in tasks.items():
        if not task.done():
            logger.debug(f"取消任务: {name}")
            task.cancel()
    
    # 等待所有任务完成取消
    if tasks:
        await asyncio.gather(*tasks.values(), return_exceptions=True)
    
    # 断开UserBot连接
    if user_bot_client is not None:
        logger.info("正在断开UserBot连接...")
        try:
            await user_bot_client.disconnect()
            logger.info("UserBot已断开连接")
        except Exception as e:
            logger.error(f"断开UserBot连接时出错: {str(e)}")
    
    # 断开SearchBot连接
    if search_bot is not None:
        logger.info("正在断开SearchBot连接...")
        try:
            await search_bot.disconnect()
            logger.info("SearchBot已断开连接")
        except Exception as e:
            logger.error(f"断开SearchBot连接时出错: {str(e)}")
    
    # 关闭FastAPI服务器
    if fastapi_server is not None:
        logger.info("正在关闭FastAPI服务器...")
        try:
            await fastapi_server.shutdown()
            logger.info("FastAPI服务器已关闭")
        except Exception as e:
            logger.error(f"关闭FastAPI服务器时出错: {str(e)}")

async def restart_userbot_task() -> None:
    """
    监听重启事件并重启User Bot任务
    
    当userbot_restart_event被设置时，停止当前的User Bot任务，
    重新创建并启动一个新的User Bot任务
    """
    global user_bot_client, tasks
    logger = logging.getLogger(__name__)
    
    try:
        while True:
            # 等待重启事件
            await userbot_restart_event.wait()
            logger.info("检测到User Bot重启事件")
            
            try:
                # 如果有正在运行的User Bot任务，先停止它
                if "UserBotTask" in tasks and not tasks["UserBotTask"].done():
                    logger.info("停止当前的User Bot任务")
                    tasks["UserBotTask"].cancel()
                    
                    # 等待任务取消完成
                    try:
                        await tasks["UserBotTask"]
                    except asyncio.CancelledError:
                        logger.info("User Bot任务已取消")
                    
                    # 断开User Bot客户端连接
                    await user_bot_client.disconnect()
                
                # 重新加载配置
                user_bot_client.reload_config()
                
                # 创建新的User Bot任务
                logger.info("创建新的User Bot任务")
                tasks["UserBotTask"] = asyncio.create_task(
                    user_bot_client.run(),
                    name="UserBotTask"
                )
                
                logger.info("User Bot已重新启动")
            except Exception as e:
                logger.error(f"重启User Bot时出错: {str(e)}")
            finally:
                # 重置重启事件
                userbot_restart_event.clear()
    except asyncio.CancelledError:
        # 处理监控任务自身被取消的情况
        logger.info("User Bot重启监控任务被取消")
        # 不重新抛出异常，让任务安静地结束

async def async_main() -> None:
    """
    主异步函数
    
    负责实例化并并发运行UserBot、SearchBot客户端和FastAPI服务器
    使用asyncio.create_task创建独立任务，以便于管理每个任务的生命周期
    """
    global user_bot_client, search_bot, fastapi_server, tasks
    
    logger = logging.getLogger(__name__)
    logger.info("正在启动Telegram中文历史消息搜索服务...")

    try:
        # 实例化UserBotClient（使用单例模式）
        user_bot_client = UserBotClient()
        # 实例化SearchBot，传递User Bot重启事件
        search_bot = SearchBot(userbot_restart_event=userbot_restart_event)
        
        logger.info("已创建UserBot和SearchBot实例")
        
        # 配置并创建FastAPI服务器
        config = uvicorn.Config(
            fastapi_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
        fastapi_server = uvicorn.Server(config)
        logger.info("已创建FastAPI服务器实例")
        
        # 创建并存储任务，使用create_task而不是直接使用gather
        # 这样我们可以在需要时单独取消任务
        tasks["UserBotTask"] = asyncio.create_task(
            user_bot_client.run(),  # 使用run方法替代start方法，以保持客户端运行
            name="UserBotTask"
        )
        tasks["SearchBotTask"] = asyncio.create_task(
            search_bot.run(),
            name="SearchBotTask"
        )
        tasks["FastAPITask"] = asyncio.create_task(
            fastapi_server.serve(),
            name="FastAPITask"
        )
        
        # 创建User Bot重启监听任务
        tasks["RestartMonitorTask"] = asyncio.create_task(
            restart_userbot_task(),
            name="RestartMonitorTask"
        )
        logger.info("已启动所有服务任务")
        
        # 等待所有任务完成
        # 使用return_exceptions=True确保即使某个任务抛出异常，其他任务也不会被取消
        await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        
    except Exception as e:
        logger.exception(f"运行客户端时发生错误: {str(e)}")
        # 出错时也确保关闭客户端
        await shutdown_clients()
        raise

def setup_signal_handlers() -> None:
    """
    设置信号处理器
    
    捕获SIGINT和SIGTERM信号，确保程序能够优雅地关闭
    """
    # 仅在非Windows平台上设置SIGTERM处理器
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

async def main() -> None:
    """
    主程序入口异步函数
    
    包含try/finally块，确保在任何情况下都能正确清理资源
    """
    try:
        await async_main()
    finally:
        # 无论是正常退出还是异常退出，都确保关闭客户端
        await shutdown_clients()

if __name__ == "__main__":
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 设置信号处理器
    setup_signal_handlers()
    
    try:
        # 启动主异步函数
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("检测到键盘中断，正在优雅关闭客户端...")
        print("\n正在关闭服务，请稍候...")
        # 注意: 当KeyboardInterrupt发生时，asyncio.run会取消所有的任务
        # 并且会调用main()中的finally块，所以shutdown_clients()会被自动调用
    except Exception as e:
        logger.exception(f"程序运行时发生错误: {str(e)}")
    finally:
        logger.info("服务已完全关闭")
        print("Telegram中文历史消息搜索服务已关闭。")
