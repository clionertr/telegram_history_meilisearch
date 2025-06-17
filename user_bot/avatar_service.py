"""
头像下载服务模块

此模块专门处理Telegram头像的下载和缓存，包括：
1. 异步头像下载
2. 并发控制和超时管理
3. 缓存管理
4. 错误处理和重试机制
"""

import asyncio
import logging
import base64
from typing import Dict, Optional, List, Any
import time

from core.async_task_manager import get_task_manager

logger = logging.getLogger(__name__)


class AvatarDownloadError(Exception):
    """头像下载异常"""
    pass


class AvatarService:
    """
    头像下载服务
    
    提供统一的头像下载和缓存管理功能
    """
    
    def __init__(self, client, max_concurrent: int = 10):
        """
        初始化头像服务
        
        Args:
            client: Telethon客户端实例
            max_concurrent: 最大并发下载数
        """
        self.client = client
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.task_manager = get_task_manager()
        
        # 头像缓存
        self._avatars_cache: Dict[int, Optional[str]] = {}
        self._download_tasks: Dict[int, asyncio.Task] = {}
        
        # 统计信息
        self._stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'cache_hits': 0,
            'timeouts': 0
        }
        
    async def download_avatar(
        self, 
        dialog_info: Dict[str, Any], 
        timeout: float = 5.0,
        force_refresh: bool = False
    ) -> Optional[str]:
        """
        下载单个头像
        
        Args:
            dialog_info: 对话信息字典
            timeout: 下载超时时间
            force_refresh: 是否强制刷新缓存
            
        Returns:
            str: Base64编码的头像数据，如果没有头像则返回None
        """
        dialog_id = dialog_info["id"]
        dialog_name = dialog_info.get("name", "Unknown")
        
        # 检查缓存
        if not force_refresh and dialog_id in self._avatars_cache:
            self._stats['cache_hits'] += 1
            logger.debug(f"从缓存返回对话 {dialog_id} ({dialog_name}) 的头像")
            return self._avatars_cache[dialog_id]
            
        # 检查是否已有正在进行的下载任务
        if dialog_id in self._download_tasks:
            existing_task = self._download_tasks[dialog_id]
            if not existing_task.done():
                logger.debug(f"等待对话 {dialog_id} 的现有下载任务完成")
                try:
                    return await existing_task
                except Exception as e:
                    logger.warning(f"等待现有下载任务失败: {e}")
                    
        # 创建新的下载任务
        task = self.task_manager.create_task(
            self._download_avatar_impl(dialog_info, timeout),
            name=f"download_avatar_{dialog_id}",
            group="avatar_downloads",
            timeout=timeout + 1.0  # 给任务管理器额外的超时缓冲
        )
        
        self._download_tasks[dialog_id] = task
        
        try:
            result = await task
            return result
        finally:
            # 清理下载任务记录
            self._download_tasks.pop(dialog_id, None)
            
    async def _download_avatar_impl(
        self, 
        dialog_info: Dict[str, Any], 
        timeout: float
    ) -> Optional[str]:
        """
        头像下载的具体实现
        
        Args:
            dialog_info: 对话信息字典
            timeout: 下载超时时间
            
        Returns:
            str: Base64编码的头像数据，如果没有头像则返回None
        """
        dialog_id = dialog_info["id"]
        dialog_name = dialog_info.get("name", "Unknown")
        
        self._stats['total_downloads'] += 1
        
        try:
            entity = dialog_info.get("entity")
            if not entity:
                logger.warning(f"对话 {dialog_id} ({dialog_name}) 没有entity信息，无法下载头像")
                self._avatars_cache[dialog_id] = None
                self._stats['failed_downloads'] += 1
                return None
                
            logger.debug(f"开始下载对话 {dialog_id} ({dialog_name}) 的头像...")
            
            # 使用信号量控制并发
            async with self.semaphore:
                # 下载头像
                photo_bytes = await asyncio.wait_for(
                    self.client.download_profile_photo(entity, file=bytes),
                    timeout=timeout
                )
                
            if photo_bytes:
                base64_string = base64.b64encode(photo_bytes).decode('utf-8')
                avatar_data = f"data:image/jpeg;base64,{base64_string}"
                
                # 缓存头像
                self._avatars_cache[dialog_id] = avatar_data
                self._stats['successful_downloads'] += 1
                
                logger.debug(f"成功下载并缓存对话 {dialog_id} ({dialog_name}) 的头像，大小: {len(photo_bytes)} 字节")
                return avatar_data
            else:
                logger.warning(f"对话 {dialog_id} ({dialog_name}) 没有头像或下载为空")
                self._avatars_cache[dialog_id] = None
                self._stats['failed_downloads'] += 1
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"下载对话 {dialog_id} ({dialog_name}) 头像超时 ({timeout}秒)")
            self._avatars_cache[dialog_id] = None
            self._stats['timeouts'] += 1
            self._stats['failed_downloads'] += 1
            return None
        except asyncio.CancelledError:
            logger.debug(f"下载对话 {dialog_id} ({dialog_name}) 头像被取消")
            raise
        except Exception as e:
            logger.warning(f"下载对话 {dialog_id} ({dialog_name}) 头像失败: {e}")
            self._avatars_cache[dialog_id] = None
            self._stats['failed_downloads'] += 1
            return None
            
    async def batch_download_avatars(
        self, 
        dialogs_info: List[Dict[str, Any]],
        timeout_per_avatar: float = 5.0,
        progress_callback: Optional[callable] = None
    ) -> Dict[int, Optional[str]]:
        """
        批量下载头像
        
        Args:
            dialogs_info: 对话信息列表
            timeout_per_avatar: 每个头像的下载超时时间
            progress_callback: 进度回调函数，接收 (completed, total) 参数
            
        Returns:
            dict: 对话ID到头像数据的映射
        """
        if not dialogs_info:
            logger.warning("对话列表为空，无法批量下载头像")
            return {}
            
        logger.info(f"开始批量下载 {len(dialogs_info)} 个对话的头像（最大并发数: {self.max_concurrent}）")
        
        # 创建下载任务
        download_tasks = []
        for dialog_info in dialogs_info:
            task = self.download_avatar(dialog_info, timeout_per_avatar)
            download_tasks.append((dialog_info["id"], task))
            
        # 执行批量下载
        results = {}
        completed = 0
        
        try:
            # 使用 asyncio.as_completed 来获取进度更新
            for dialog_id, task in download_tasks:
                try:
                    result = await task
                    results[dialog_id] = result
                    completed += 1
                    
                    # 调用进度回调
                    if progress_callback:
                        try:
                            progress_callback(completed, len(dialogs_info))
                        except Exception as e:
                            logger.warning(f"进度回调函数出错: {e}")
                            
                except Exception as e:
                    logger.warning(f"下载对话 {dialog_id} 头像时发生异常: {e}")
                    results[dialog_id] = None
                    completed += 1
                    
                    if progress_callback:
                        try:
                            progress_callback(completed, len(dialogs_info))
                        except Exception as e:
                            logger.warning(f"进度回调函数出错: {e}")
                            
        except Exception as e:
            logger.error(f"批量下载头像时发生错误: {e}")
            
        # 统计结果
        success_count = sum(1 for result in results.values() if result is not None)
        no_avatar_count = sum(1 for result in results.values() if result is None)
        
        logger.info(f"批量头像下载完成 - 成功: {success_count}, 无头像: {no_avatar_count}")
        
        return results
        
    def get_cached_avatar(self, dialog_id: int) -> Optional[str]:
        """
        从缓存获取头像
        
        Args:
            dialog_id: 对话ID
            
        Returns:
            str: Base64编码的头像数据，如果没有则返回None
        """
        return self._avatars_cache.get(dialog_id)
        
    def clear_cache(self) -> None:
        """清除头像缓存"""
        self._avatars_cache.clear()
        logger.info("头像缓存已清除")
        
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._avatars_cache)
        
    def get_stats(self) -> Dict[str, Any]:
        """
        获取下载统计信息
        
        Returns:
            dict: 包含下载统计的字典
        """
        return {
            **self._stats,
            'cache_size': len(self._avatars_cache),
            'active_downloads': len(self._download_tasks),
            'max_concurrent': self.max_concurrent
        }
        
    async def cancel_all_downloads(self) -> None:
        """取消所有正在进行的下载任务"""
        if not self._download_tasks:
            return
            
        logger.info(f"取消 {len(self._download_tasks)} 个正在进行的头像下载任务")
        
        # 通过任务管理器取消整个下载组
        await self.task_manager.cancel_group("avatar_downloads")
        
        # 清理下载任务记录
        self._download_tasks.clear()
        
        logger.info("所有头像下载任务已取消")
