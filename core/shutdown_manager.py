"""
优雅关闭管理器模块

此模块提供统一的应用程序关闭管理，包括：
1. 资源清理顺序管理
2. 超时控制
3. 异常处理
4. 关闭状态跟踪
"""

import asyncio
import logging
import signal
import sys
from typing import List, Callable, Awaitable, Optional, Any
from contextlib import asynccontextmanager
import time

logger = logging.getLogger(__name__)


class ShutdownHandler:
    """关闭处理器接口"""
    
    def __init__(self, name: str, handler: Callable[[], Awaitable[None]], timeout: float = 10.0):
        self.name = name
        self.handler = handler
        self.timeout = timeout
        

class ShutdownManager:
    """
    优雅关闭管理器
    
    管理应用程序的优雅关闭流程，确保所有资源都能正确清理
    """
    
    def __init__(self):
        self._handlers: List[ShutdownHandler] = []
        self._shutdown_event = asyncio.Event()
        self._is_shutting_down = False
        self._shutdown_start_time: Optional[float] = None
        self._signal_handlers_installed = False
        
    def add_handler(
        self, 
        name: str, 
        handler: Callable[[], Awaitable[None]], 
        timeout: float = 10.0
    ) -> None:
        """
        添加关闭处理器
        
        Args:
            name: 处理器名称
            handler: 异步处理函数
            timeout: 处理器超时时间
        """
        if self._is_shutting_down:
            logger.warning(f"系统正在关闭，无法添加新的关闭处理器: {name}")
            return
            
        shutdown_handler = ShutdownHandler(name, handler, timeout)
        self._handlers.append(shutdown_handler)
        logger.debug(f"添加关闭处理器: {name} (超时: {timeout}秒)")
        
    def remove_handler(self, name: str) -> bool:
        """
        移除关闭处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, handler in enumerate(self._handlers):
            if handler.name == name:
                del self._handlers[i]
                logger.debug(f"移除关闭处理器: {name}")
                return True
        return False
        
    def install_signal_handlers(self) -> None:
        """安装信号处理器"""
        if self._signal_handlers_installed:
            return
            
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.info(f"接收到 {signal_name} 信号，开始优雅关闭...")
            
            # 在事件循环中设置关闭事件
            try:
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self._shutdown_event.set)
            except RuntimeError:
                # 如果没有运行的事件循环，直接设置事件
                self._shutdown_event.set()
                
        # 设置SIGINT处理器 (Ctrl+C)
        signal.signal(signal.SIGINT, signal_handler)
        
        # 仅在非Windows平台上设置SIGTERM处理器
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, signal_handler)
            
        self._signal_handlers_installed = True
        logger.debug("信号处理器已安装")
        
    async def wait_for_shutdown(self) -> None:
        """等待关闭信号"""
        await self._shutdown_event.wait()
        
    async def shutdown(self, reason: str = "Manual shutdown") -> None:
        """
        执行优雅关闭
        
        Args:
            reason: 关闭原因
        """
        if self._is_shutting_down:
            logger.warning("关闭流程已在进行中")
            return
            
        self._is_shutting_down = True
        self._shutdown_start_time = time.time()
        self._shutdown_event.set()
        
        logger.info(f"开始优雅关闭流程: {reason}")
        logger.info(f"共有 {len(self._handlers)} 个关闭处理器需要执行")
        
        # 按注册顺序的逆序执行关闭处理器
        for i, handler in enumerate(reversed(self._handlers)):
            handler_index = len(self._handlers) - i
            logger.info(f"执行关闭处理器 {handler_index}/{len(self._handlers)}: {handler.name}")
            
            try:
                await asyncio.wait_for(handler.handler(), timeout=handler.timeout)
                logger.info(f"关闭处理器 {handler.name} 执行成功")
            except asyncio.TimeoutError:
                logger.error(f"关闭处理器 {handler.name} 执行超时 ({handler.timeout}秒)")
            except Exception as e:
                logger.error(f"关闭处理器 {handler.name} 执行失败: {e}", exc_info=True)
                
        shutdown_duration = time.time() - self._shutdown_start_time
        logger.info(f"优雅关闭流程完成，耗时 {shutdown_duration:.2f} 秒")
        
    def trigger_shutdown(self, reason: str = "External trigger") -> None:
        """
        触发关闭流程（非异步）
        
        Args:
            reason: 关闭原因
        """
        if not self._is_shutting_down:
            logger.info(f"触发关闭: {reason}")
            self._shutdown_event.set()
            
    @asynccontextmanager
    async def managed_lifecycle(self):
        """
        托管生命周期上下文管理器
        
        在上下文中运行应用程序，自动处理关闭流程
        """
        try:
            # 安装信号处理器
            self.install_signal_handlers()
            yield self
        finally:
            # 确保执行关闭流程
            if not self._is_shutting_down:
                await self.shutdown("Context exit")
                
    def is_shutting_down(self) -> bool:
        """检查是否正在关闭"""
        return self._is_shutting_down
        
    def get_status(self) -> dict:
        """
        获取关闭管理器状态
        
        Returns:
            dict: 状态信息
        """
        return {
            'is_shutting_down': self._is_shutting_down,
            'handlers_count': len(self._handlers),
            'signal_handlers_installed': self._signal_handlers_installed,
            'shutdown_start_time': self._shutdown_start_time,
            'handlers': [
                {
                    'name': handler.name,
                    'timeout': handler.timeout
                }
                for handler in self._handlers
            ]
        }


# 全局关闭管理器实例
_shutdown_manager: Optional[ShutdownManager] = None


def get_shutdown_manager() -> ShutdownManager:
    """获取全局关闭管理器实例"""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = ShutdownManager()
    return _shutdown_manager


class TelethonClientManager:
    """
    Telethon客户端管理器
    
    专门处理Telethon客户端的优雅关闭
    """
    
    @staticmethod
    async def disconnect_client(client, client_name: str = "TelegramClient") -> None:
        """
        优雅地断开Telethon客户端连接
        
        Args:
            client: Telethon客户端实例
            client_name: 客户端名称（用于日志）
        """
        if not client:
            logger.debug(f"{client_name} 客户端为空，无需断开")
            return
            
        if not client.is_connected():
            logger.debug(f"{client_name} 已经断开连接")
            return
            
        logger.info(f"开始断开 {client_name} 连接...")
        
        try:
            # 给客户端一些时间来完成正在进行的操作
            await asyncio.sleep(0.1)
            
            # 使用优雅关闭，等待所有内部任务完成
            disconnect_task = asyncio.create_task(client.disconnect())
            
            # 设置超时，避免无限等待
            await asyncio.wait_for(disconnect_task, timeout=5.0)
            
            logger.info(f"{client_name} 连接已优雅关闭")
            
        except asyncio.TimeoutError:
            logger.warning(f"{client_name} 优雅关闭超时，尝试强制断开")
            
            # 如果优雅关闭超时，尝试强制断开
            try:
                if hasattr(client, '_disconnect'):
                    await asyncio.wait_for(client._disconnect(), timeout=2.0)
                    logger.info(f"{client_name} 强制断开成功")
                else:
                    logger.warning(f"{client_name} 没有 _disconnect 方法，无法强制断开")
            except Exception as force_e:
                logger.error(f"强制断开 {client_name} 也失败: {force_e}")
                
        except Exception as e:
            logger.error(f"断开 {client_name} 连接时出错: {e}")
            
            # 尝试强制断开
            try:
                if hasattr(client, '_disconnect'):
                    await client._disconnect()
                    logger.info(f"{client_name} 强制断开成功")
            except Exception as force_e:
                logger.error(f"强制断开 {client_name} 也失败: {force_e}")
                
        # 给一些时间让内部任务清理
        await asyncio.sleep(0.1)
