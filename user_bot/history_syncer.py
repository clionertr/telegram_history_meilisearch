"""
Telegram → Meilisearch 同步引擎（双光标 + 安全重叠窗口）

该模块完全替换旧版 HistorySyncer 逻辑，核心特性：
1. forward_sync：向前增量流水线，持续写入新消息；
2. backward_sync：向后回溯流水线，带重叠窗口补齐历史空洞；
3. 共享状态文件 config/sync_points.json，原子写入防并发冲突；
4. 支持 cutoff_ts → cutoff_id 首次换算；
5. 自动处理 FloodWait；
6. 兼容 user_bot.client 既有入口 initial_sync_all_whitelisted_chats。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import Message, User

from core.config_manager import ConfigManager
from core.meilisearch_service import MeiliSearchService
from core.models import MeiliMessageDoc
from user_bot.utils import generate_message_link, format_sender_name

# --------------------------- 常量 ---------------------------
STATE_FILE = "config/sync_points.json"
POLL_INTERVAL = 3          # forward_sync 拉取间隔（秒）
DEFAULT_OVERLAP = 100       # backward_sync 批次重叠

_logger = logging.getLogger(__name__)

# --------------------------- 文件级别锁 ---------------------------
_FILE_LOCK: Optional[asyncio.Lock] = None

def _get_file_lock() -> asyncio.Lock:
    global _FILE_LOCK
    if _FILE_LOCK is None:
        _FILE_LOCK = asyncio.Lock()
    return _FILE_LOCK

# --------------------------- 工具函数 ---------------------------

def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _logger.warning(f"读取状态文件 {path} 失败: {e}")
        return {}

def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)

# --------------------------- 同步器 ---------------------------

class HistorySyncer:
    """负责单个 chat 的双光标同步。"""

    def __init__(
        self,
        client: TelegramClient,
        meili_service: MeiliSearchService,
        chat_id: int,
        cutoff_ts: int = 0,
        overlap: int = DEFAULT_OVERLAP,
    ) -> None:
        self.client = client
        self.meili_service = meili_service
        self.chat_id = chat_id
        self.overlap = overlap
        self._state_lock = asyncio.Lock()

        # 加载或初始化状态
        all_state = _read_json(STATE_FILE)
        self.state: Dict[str, Any] = all_state.get(str(chat_id), {
            "chat_id": chat_id,
            "cutoff_ts": cutoff_ts,
            "cutoff_id": 0,
            "last_newest_id": 0,
            "next_oldest_id": 0,
            "overlap": overlap,
        })

    # ----------------------- 状态持久化 -----------------------
    async def _persist_state(self) -> None:
        async with _get_file_lock():
            all_state = _read_json(STATE_FILE)
            all_state[str(self.chat_id)] = self.state
            Path(os.path.dirname(STATE_FILE)).mkdir(parents=True, exist_ok=True)
            _atomic_write_json(STATE_FILE, all_state)

    # ----------------------- 初始化 -----------------------
    async def initialize(self) -> None:
        if self.state.get("cutoff_id", 0) == 0 and self.state.get("cutoff_ts", 0) > 0:
            first = await self.client.get_messages(self.chat_id, limit=1, offset_date=self.state["cutoff_ts"])
            self.state["cutoff_id"] = first[0].id if first else 0

        if self.state.get("last_newest_id", 0) == 0 or self.state.get("next_oldest_id", 0) == 0:
            top = await self.client.get_messages(self.chat_id, limit=1)
            top_id = top[0].id if top else 0
            self.state["last_newest_id"] = top_id
            self.state["next_oldest_id"] = top_id

        await self._persist_state()
        _logger.info(f"[{self.chat_id}] 初始化完成: {self.state}")

    # ----------------------- 索引 -----------------------
    async def _index_to_meili(self, msg: Message) -> None:
        if not (msg.text or msg.message):
            return

        sender_name: Optional[str] = None
        if msg.sender and isinstance(msg.sender, User):
            sender_name = format_sender_name(msg.sender.first_name, getattr(msg.sender, "last_name", None))

        chat_title = getattr(msg.chat, "title", None) if msg.chat else None

        if msg.is_private:
            chat_type = "user"
        elif msg.is_group:
            chat_type = "group"
        else:
            chat_type = "channel"

        doc = MeiliMessageDoc(
            id=f"{msg.chat_id}_{msg.id}",
            message_id=msg.id,
            chat_id=msg.chat_id,
            chat_title=chat_title,
            chat_type=chat_type,
            sender_id=msg.sender_id or 0,
            sender_name=sender_name,
            text=msg.text or msg.message or "",
            date=int(msg.date.timestamp()),
            message_link=generate_message_link(msg.chat_id, msg.id),
        )

        try:
            self.meili_service.index_message(doc)
        except Exception as e:
            _logger.error(f"[Meili] 索引失败 chat={self.chat_id} id={msg.id}: {e}")

    # ----------------------- forward_sync -----------------------
    async def _forward_sync(self) -> None:
        while True:
            try:
                top = await self.client.get_messages(self.chat_id, limit=1)
                top_id = top[0].id if top else 0

                async with self._state_lock:
                    last_newest = self.state["last_newest_id"]

                if top_id > last_newest:
                    async for msg in self.client.iter_messages(self.chat_id, min_id=last_newest, limit=100):
                        await self._index_to_meili(msg)
                    async with self._state_lock:
                        self.state["last_newest_id"] = top_id
                        await self._persist_state()
                await asyncio.sleep(POLL_INTERVAL)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                _logger.error(f"[{self.chat_id}] forward_sync error: {e}", exc_info=True)
                await asyncio.sleep(5)

    # ----------------------- backward_sync -----------------------
    async def _backward_sync(self) -> None:
        while True:
            async with self._state_lock:
                next_oldest = self.state["next_oldest_id"]
                cutoff_id = self.state["cutoff_id"]
                overlap = self.state["overlap"]

            if cutoff_id == 0 or next_oldest <= cutoff_id:
                await asyncio.sleep(3600)
                continue

            try:
                batch: List[Message] = []
                async for msg in self.client.iter_messages(self.chat_id, offset_id=next_oldest, limit=100):
                    if msg.id <= cutoff_id:
                        break
                    batch.append(msg)
                    await self._index_to_meili(msg)

                smallest = min((m.id for m in batch), default=cutoff_id)
                new_next = max(smallest - overlap, cutoff_id)

                async with self._state_lock:
                    self.state["next_oldest_id"] = new_next
                    await self._persist_state()
                await asyncio.sleep(0.2)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                _logger.error(f"[{self.chat_id}] backward_sync error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def run(self) -> None:
        await self.initialize()
        await asyncio.gather(self._forward_sync(), self._backward_sync())

# ----------------------- 兼容入口 -----------------------
async def initial_sync_all_whitelisted_chats(
    client: Optional[TelegramClient] = None,
    config_manager: Optional[ConfigManager] = None,
    meilisearch_service: Optional[MeiliSearchService] = None,
    cutoff_ts: Optional[int] = None,
    **__kwargs,
) -> Dict[int, Tuple[int, int]]:
    config_manager = config_manager or ConfigManager()
    meilisearch_service = meilisearch_service or _create_meili(config_manager)
    if client is None:
        raise RuntimeError("TelegramClient 未提供")

    results: Dict[int, Tuple[int, int]] = {}
    for chat_id in config_manager.get_whitelist():
        syncer = HistorySyncer(
            client=client,
            meili_service=meilisearch_service,
            chat_id=chat_id,
            cutoff_ts=cutoff_ts or 0,
        )
        asyncio.create_task(syncer.run(), name=f"sync_chat_{chat_id}")
        results[chat_id] = (0, 0)  # 占位返回值，保持旧接口签名
        _logger.info(f"已启动 chat {chat_id} 同步任务")
    return results

# ----------------------- 内部辅助 -----------------------

def _create_meili(config: ConfigManager) -> MeiliSearchService:
    host = config.get_env("MEILISEARCH_HOST") or config.get_config("MeiliSearch", "HOST", "http://localhost:7700")
    api_key = config.get_env("MEILISEARCH_API_KEY") or config.get_config("MeiliSearch", "API_KEY")
    return MeiliSearchService(host=host, api_key=api_key) 