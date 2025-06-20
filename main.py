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
from core.shutdown_manager import get_shutdown_manager
from core.async_task_manager import get_task_manager

# 全局变量，存储客户端实例，用于在程序退出时确保它们被断开连接
user_bot_client: Optional[UserBotClient] = None
search_bot: Optional[SearchBot] = None
# 存储任务对象，用于在需要时取消任务
tasks: Dict[str, asyncio.Task] = {}
# FastAPI 服务器实例
fastapi_server: Optional[uvicorn.Server] = None
# User Bot 重启事件
userbot_restart_event: asyncio.Event = asyncio.Event()
# 关闭事件，用于优雅关闭
shutdown_event: asyncio.Event = asyncio.Event()

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

def signal_handler(signum, frame):
    """
    信号处理器，用于优雅关闭
    """
    logger = logging.getLogger(__name__)
    signal_name = signal.Signals(signum).name
    logger.info(f"接收到 {signal_name} 信号，开始优雅关闭...")

    # 通过关闭管理器触发关闭
    shutdown_manager = get_shutdown_manager()
    shutdown_manager.trigger_shutdown(f"Signal {signal_name}")

    # 设置关闭事件（向后兼容）
    if not shutdown_event.is_set():
        shutdown_event.set()

async def shutdown_clients() -> None:
    """
    关闭所有客户端连接

    使用新的关闭管理器确保所有资源优雅地关闭
    """
    logger = logging.getLogger(__name__)

    # 获取管理器实例
    shutdown_manager = get_shutdown_manager()
    task_manager = get_task_manager()

    logger.info("开始优雅关闭流程...")

    try:
        # 使用关闭管理器执行优雅关闭
        await shutdown_manager.shutdown("Application shutdown")

        # 关闭任务管理器
        await task_manager.shutdown(timeout=10.0)

        # 关闭FastAPI服务器
        if fastapi_server is not None:
            logger.info("正在关闭FastAPI服务器...")
            try:
                await fastapi_server.shutdown()
                logger.info("FastAPI服务器已关闭")
            except Exception as e:
                logger.error(f"关闭FastAPI服务器时出错: {str(e)}")

    except Exception as e:
        logger.error(f"优雅关闭过程中出错: {e}")

        # 如果优雅关闭失败，尝试强制关闭
        logger.info("尝试强制关闭...")

        # 强制断开UserBot连接
        if user_bot_client is not None:
            try:
                await user_bot_client.disconnect()
            except Exception as e:
                logger.error(f"强制断开UserBot连接时出错: {str(e)}")

        # 强制断开SearchBot连接
        if search_bot is not None:
            try:
                await search_bot.disconnect()
            except Exception as e:
                logger.error(f"强制断开SearchBot连接时出错: {str(e)}")

        # 强制取消所有任务
        for name, task in tasks.items():
            if not task.done():
                logger.debug(f"强制取消任务: {name}")
                task.cancel()

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
    使用新的任务管理器和关闭管理器来确保优雅关闭
    """
    global user_bot_client, search_bot, fastapi_server, tasks

    logger = logging.getLogger(__name__)
    logger.info("正在启动Telegram中文历史消息搜索服务...")

    # 获取管理器实例
    shutdown_manager = get_shutdown_manager()
    task_manager = get_task_manager()

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
        
        # 使用任务管理器创建任务
        tasks["UserBotTask"] = task_manager.create_task(
            user_bot_client.run(),
            name="UserBotTask",
            group="main_services"
        )
        tasks["SearchBotTask"] = task_manager.create_task(
            search_bot.run(),
            name="SearchBotTask",
            group="main_services"
        )
        tasks["FastAPITask"] = task_manager.create_task(
            fastapi_server.serve(),
            name="FastAPITask",
            group="main_services"
        )

        # 创建User Bot重启监听任务
        tasks["RestartMonitorTask"] = task_manager.create_task(
            restart_userbot_task(),
            name="RestartMonitorTask",
            group="monitoring"
        )
        logger.info("已启动所有服务任务")
        
        # 安装信号处理器并等待关闭信号
        shutdown_manager.install_signal_handlers()

        # 创建关闭监听任务
        async def wait_for_shutdown():
            await shutdown_manager.wait_for_shutdown()
            logger.info("接收到关闭信号，开始关闭所有任务...")
            # 通过任务管理器取消所有任务
            await task_manager.cancel_group("main_services")
            await task_manager.cancel_group("monitoring")

        # 将关闭监听任务也加入到任务列表中
        tasks["ShutdownMonitor"] = task_manager.create_task(
            wait_for_shutdown(),
            name="ShutdownMonitor",
            group="system"
        )
        
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
    # 设置SIGINT处理器 (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 仅在非Windows平台上设置SIGTERM处理器
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, signal_handler)

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
        # 运行主程序
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        print("\n正在关闭服务，请稍候...")
    except Exception as e:
        logger.error(f"程序运行时发生未处理的错误: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Telegram中文历史消息搜索服务已关闭")
        print("服务已完全关闭。")

