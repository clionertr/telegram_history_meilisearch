"""
异步任务管理器模块

此模块提供统一的异步任务管理功能，包括：
1. 任务创建和跟踪
2. 任务取消和清理
3. 超时控制
4. 异常处理和日志记录
"""

import asyncio
import logging
import weakref
from typing import Dict, Set, Optional, Any, Callable, Awaitable
from contextlib import asynccontextmanager
import time

logger = logging.getLogger(__name__)


class AsyncTaskManager:
    """
    异步任务管理器
    
    提供统一的异步任务管理，确保所有任务都能被正确跟踪和清理
    """
    
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._task_groups: Dict[str, Set[str]] = {}
        self._shutdown_event = asyncio.Event()
        self._is_shutting_down = False
        
    def create_task(
        self, 
        coro: Awaitable[Any], 
        name: Optional[str] = None,
        group: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> asyncio.Task:
        """
        创建并跟踪一个异步任务
        
        Args:
            coro: 协程对象
            name: 任务名称，用于标识和日志
            group: 任务组名，用于批量管理
            timeout: 任务超时时间（秒）
            
        Returns:
            asyncio.Task: 创建的任务对象
        """
        if self._is_shutting_down:
            logger.warning(f"系统正在关闭，拒绝创建新任务: {name}")
            raise RuntimeError("TaskManager is shutting down")
            
        # 如果指定了超时，包装协程
        if timeout:
            coro = asyncio.wait_for(coro, timeout=timeout)
            
        task = asyncio.create_task(coro, name=name)
        
        # 生成唯一的任务ID
        task_id = name or f"task_{id(task)}"
        if task_id in self._tasks:
            task_id = f"{task_id}_{int(time.time() * 1000000) % 1000000}"
            
        self._tasks[task_id] = task
        
        # 添加到任务组
        if group:
            if group not in self._task_groups:
                self._task_groups[group] = set()
            self._task_groups[group].add(task_id)
            
        # 添加完成回调，自动清理已完成的任务
        def cleanup_task(t):
            try:
                if task_id in self._tasks:
                    del self._tasks[task_id]
                    
                # 从任务组中移除
                if group and group in self._task_groups:
                    self._task_groups[group].discard(task_id)
                    if not self._task_groups[group]:
                        del self._task_groups[group]
                        
                # 记录任务完成状态
                if t.cancelled():
                    logger.debug(f"任务 {task_id} 被取消")
                elif t.exception():
                    logger.warning(f"任务 {task_id} 异常完成: {t.exception()}")
                else:
                    logger.debug(f"任务 {task_id} 正常完成")
            except Exception as e:
                logger.error(f"清理任务 {task_id} 时出错: {e}")
                
        task.add_done_callback(cleanup_task)
        
        logger.debug(f"创建任务: {task_id} (组: {group})")
        return task
        
    def get_task(self, task_id: str) -> Optional[asyncio.Task]:
        """获取指定ID的任务"""
        return self._tasks.get(task_id)
        
    def get_tasks_in_group(self, group: str) -> Dict[str, asyncio.Task]:
        """获取指定组中的所有任务"""
        if group not in self._task_groups:
            return {}
        return {
            task_id: self._tasks[task_id] 
            for task_id in self._task_groups[group] 
            if task_id in self._tasks
        }
        
    async def cancel_task(self, task_id: str, timeout: float = 5.0) -> bool:
        """
        取消指定的任务
        
        Args:
            task_id: 任务ID
            timeout: 等待取消完成的超时时间
            
        Returns:
            bool: 是否成功取消
        """
        task = self._tasks.get(task_id)
        if not task or task.done():
            return True
            
        logger.debug(f"取消任务: {task_id}")
        task.cancel()
        
        try:
            await asyncio.wait_for(task, timeout=timeout)
            return True
        except asyncio.CancelledError:
            return True
        except asyncio.TimeoutError:
            logger.warning(f"等待任务 {task_id} 取消超时")
            return False
        except Exception as e:
            logger.error(f"取消任务 {task_id} 时出错: {e}")
            return False
            
    async def cancel_group(self, group: str, timeout: float = 5.0) -> int:
        """
        取消指定组中的所有任务
        
        Args:
            group: 任务组名
            timeout: 等待取消完成的超时时间
            
        Returns:
            int: 成功取消的任务数量
        """
        tasks = self.get_tasks_in_group(group)
        if not tasks:
            return 0
            
        logger.info(f"取消任务组 {group} 中的 {len(tasks)} 个任务")
        
        # 取消所有任务
        for task in tasks.values():
            if not task.done():
                task.cancel()
                
        # 等待所有任务完成取消
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks.values(), return_exceptions=True),
                timeout=timeout
            )
            return len(tasks)
        except asyncio.TimeoutError:
            logger.warning(f"等待任务组 {group} 取消超时")
            return sum(1 for task in tasks.values() if task.done())
            
    async def shutdown(self, timeout: float = 10.0) -> None:
        """
        关闭任务管理器，取消所有正在运行的任务
        
        Args:
            timeout: 等待所有任务完成的超时时间
        """
        if self._is_shutting_down:
            return
            
        self._is_shutting_down = True
        self._shutdown_event.set()
        
        if not self._tasks:
            logger.info("没有正在运行的任务需要清理")
            return
            
        logger.info(f"开始关闭任务管理器，共有 {len(self._tasks)} 个任务")
        
        # 取消所有任务
        for task_id, task in self._tasks.items():
            if not task.done():
                logger.debug(f"取消任务: {task_id}")
                task.cancel()
                
        # 等待所有任务完成
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks.values(), return_exceptions=True),
                    timeout=timeout
                )
                logger.info("所有任务已成功取消")
            except asyncio.TimeoutError:
                pending_count = sum(1 for task in self._tasks.values() if not task.done())
                logger.warning(f"等待任务取消超时，仍有 {pending_count} 个任务未完成")
                
        # 清理所有数据结构
        self._tasks.clear()
        self._task_groups.clear()
        
    @asynccontextmanager
    async def task_group(self, group_name: str):
        """
        任务组上下文管理器
        
        在上下文中创建的任务会自动添加到指定组中，
        退出上下文时会自动取消组中的所有任务
        """
        try:
            yield group_name
        finally:
            await self.cancel_group(group_name)
            
    def get_status(self) -> Dict[str, Any]:
        """
        获取任务管理器状态
        
        Returns:
            dict: 包含任务统计信息的字典
        """
        total_tasks = len(self._tasks)
        running_tasks = sum(1 for task in self._tasks.values() if not task.done())
        completed_tasks = total_tasks - running_tasks
        
        groups_info = {}
        for group, task_ids in self._task_groups.items():
            group_tasks = [self._tasks[tid] for tid in task_ids if tid in self._tasks]
            groups_info[group] = {
                'total': len(group_tasks),
                'running': sum(1 for task in group_tasks if not task.done()),
                'completed': sum(1 for task in group_tasks if task.done())
            }
            
        return {
            'total_tasks': total_tasks,
            'running_tasks': running_tasks,
            'completed_tasks': completed_tasks,
            'groups': groups_info,
            'is_shutting_down': self._is_shutting_down
        }


# 全局任务管理器实例
_task_manager: Optional[AsyncTaskManager] = None


def get_task_manager() -> AsyncTaskManager:
    """获取全局任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
    return _task_manager
