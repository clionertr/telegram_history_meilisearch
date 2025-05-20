"""
Meilisearch 服务模块

此模块提供与 Meilisearch 交互的功能，包括：
1. 初始化 Meilisearch 客户端
2. 配置索引设置
3. 索引消息（单条或批量）
4. 搜索消息
5. 删除消息（可选）
"""

import logging
from typing import List, Optional, Dict, Any, Union

import meilisearch
from pydantic import BaseModel

from core.models import MeiliMessageDoc


class MeiliSearchService:
    """
    Meilisearch 服务类
    
    负责与 Meilisearch 搜索引擎交互，提供消息索引、搜索和管理功能
    """
    
    def __init__(self, host: str, api_key: Optional[str] = None, index_name: str = "telegram_messages") -> None:
        """
        初始化 Meilisearch 服务
        
        Args:
            host: Meilisearch 服务的主机地址，如 http://localhost:7700
            api_key: Meilisearch 的 API Key，用于认证，可选
            index_name: 索引名称，默认为 telegram_messages
        """
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.api_key = api_key
        self.index_name = index_name
        
        # 初始化 Meilisearch 客户端
        self.client = meilisearch.Client(self.host, self.api_key)
        self.logger.info(f"已连接到 Meilisearch 服务: {self.host}")
        
        # 获取或创建索引
        self.index = self.client.index(self.index_name)
        self.logger.info(f"使用索引: {self.index_name}")
        
        # 确保索引设置正确
        self.ensure_index_setup()
    
    def ensure_index_setup(self) -> None:
        """
        确保索引存在并配置正确
        
        检查索引是否存在，不存在则创建。
        配置索引的可搜索属性、可过滤属性、可排序属性和排序规则。
        """
        # 获取所有索引
        indexes = self.client.get_indexes()
        
        # 兼容不同版本 Meilisearch API 的返回结构
        # 如果 indexes 是字典（新版 API），则尝试从不同的可能键中获取索引列表
        # 如果 indexes 有 .results 属性（旧版 API），则使用该属性
        if hasattr(indexes, 'results'):
            # 旧版 API 结构
            index_list = indexes.results
            index_names = [index.uid for index in index_list]
        else:
            # 新版 API 结构 - indexes 是字典
            self.logger.debug(f"Meilisearch get_indexes 返回的是字典: {indexes}")
            
            # 尝试获取索引列表 - 可能存在于不同的键下或直接是列表
            if isinstance(indexes, list):
                index_list = indexes
            elif isinstance(indexes, dict):
                # 尝试常见的键名
                if 'results' in indexes:
                    index_list = indexes['results']
                elif 'items' in indexes:
                    index_list = indexes['items']
                else:
                    # 如果没有找到预期的键，可能索引列表直接就是字典值
                    self.logger.warning("无法确定 Meilisearch 索引列表位置，尝试使用整个返回值")
                    index_list = indexes
            else:
                self.logger.warning(f"Meilisearch get_indexes 返回了未知类型: {type(indexes)}")
                index_list = []
            
            # 从索引列表中提取 uid - 处理可能每个索引是对象或字典的情况
            index_names = []
            for index_item in index_list:
                if hasattr(index_item, 'uid'):
                    index_names.append(index_item.uid)
                elif isinstance(index_item, dict) and 'uid' in index_item:
                    index_names.append(index_item['uid'])
        
        # 检查是否需要创建索引
        if self.index_name not in index_names:
            self.logger.info(f"索引 {self.index_name} 不存在，正在创建...")
            self.client.create_index(self.index_name)
        
        # 配置索引设置
        # 可搜索属性 - text 优先级最高
        self.index.update_searchable_attributes([
            "text",
            "sender_name",
            "chat_title"
        ])
        self.logger.info("已配置可搜索属性: ['text', 'sender_name', 'chat_title']")
        
        # 可过滤属性
        self.index.update_filterable_attributes([
            "chat_id",
            "chat_type",
            "sender_id",
            "date"
        ])
        self.logger.info("已配置可过滤属性: ['chat_id', 'chat_type', 'sender_id', 'date']")
        
        # 可排序属性
        self.index.update_sortable_attributes([
            "date"
        ])
        self.logger.info("已配置可排序属性: ['date']")
        
        # 排序规则 - 使用默认规则，适合中文搜索
        self.index.update_ranking_rules([
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness"
        ])
        self.logger.info("已配置排序规则: ['words', 'typo', 'proximity', 'attribute', 'sort', 'exactness']")
        
        # 日志记录关于停用词和同义词
        self.logger.info("注意: stopWords(停用词)和synonyms(同义词)配置不在初始设置中，可通过单独的方法配置")
    
    def index_message(self, message_doc: MeiliMessageDoc) -> dict:
        """
        索引单条消息
        
        Args:
            message_doc: 消息文档，MeiliMessageDoc Pydantic 模型实例
            
        Returns:
            Meilisearch 的响应字典，通常包含任务信息
        """
        # 将 Pydantic 模型转换为字典
        doc_dict = message_doc.model_dump()
        
        # 添加到 Meilisearch 索引
        result = self.index.add_documents([doc_dict])
        self.logger.debug(f"已索引消息: {message_doc.id}, 任务ID: {result['taskUid']}")
        
        return result
    
    def index_messages_bulk(self, message_docs: List[MeiliMessageDoc]) -> dict:
        """
        批量索引消息
        
        Args:
            message_docs: 消息文档列表，每项为 MeiliMessageDoc Pydantic 模型实例
            
        Returns:
            Meilisearch 的响应字典，通常包含任务信息
        """
        if not message_docs:
            self.logger.warning("批量索引时提供的消息列表为空")
            return {"message": "No documents to index"}
        
        # 将所有 Pydantic 模型转换为字典列表
        docs_dict = [doc.model_dump() for doc in message_docs]
        
        # 批量添加到 Meilisearch 索引
        result = self.index.add_documents(docs_dict)
        self.logger.info(f"已批量索引 {len(message_docs)} 条消息，任务ID: {result['taskUid']}")
        
        return result
    
    def search(self, query: str, filters: Optional[str] = None, sort: Optional[List[str]] = None,
               page: int = 1, hits_per_page: int = 10) -> dict:
        """
        搜索消息
        
        Args:
            query: 搜索关键词
            filters: Meilisearch 过滤字符串，例如 "chat_id = 12345 AND date > 1672531200"
            sort: 排序规则列表，例如 ["date:desc"]
            page: 页码，从 1 开始
            hits_per_page: 每页结果数
            
        Returns:
            Meilisearch 的搜索结果字典
        """
        # 构建搜索参数
        search_params: Dict[str, Any] = {
            "page": page,
            "hitsPerPage": hits_per_page
        }
        
        # 添加过滤条件
        if filters:
            search_params["filter"] = filters
        
        # 添加排序规则
        if sort:
            search_params["sort"] = sort
        
        # 执行搜索
        self.logger.debug(f"执行搜索: 关键词='{query}', 参数={search_params}")
        results = self.index.search(query, search_params)
        
        self.logger.info(f"搜索 '{query}' 找到 {results['estimatedTotalHits']} 条结果，"
                        f"处理时间: {results['processingTimeMs']}ms")
        
        return results
    
    def delete_message(self, document_id: str) -> dict:
        """
        删除单条消息
        
        Args:
            document_id: 文档ID，通常是 MeiliMessageDoc.id
            
        Returns:
            Meilisearch 的响应字典，通常包含任务信息
        """
        result = self.index.delete_document(document_id)
        self.logger.info(f"已删除消息: {document_id}, 任务ID: {result['taskUid']}")
        
        return result
    
    def update_stop_words(self, stop_words: List[str]) -> dict:
        """
        更新停用词列表
        
        停用词是搜索时会被忽略的常见词，可以提高搜索相关性。
        
        Args:
            stop_words: 停用词列表
            
        Returns:
            Meilisearch 的响应字典
        """
        result = self.index.update_stop_words(stop_words)
        self.logger.info(f"已更新停用词列表，词数: {len(stop_words)}, 任务ID: {result['taskUid']}")
        
        return result
    
    def update_synonyms(self, synonyms: Dict[str, List[str]]) -> dict:
        """
        更新同义词词典
        
        同义词可以扩展搜索匹配范围，例如 {"大学": ["高校", "学府"]}
        
        Args:
            synonyms: 同义词词典，键为主词，值为同义词列表
            
        Returns:
            Meilisearch 的响应字典
        """
        result = self.index.update_synonyms(synonyms)
        self.logger.info(f"已更新同义词词典，词组数: {len(synonyms)}, 任务ID: {result['taskUid']}")
        
        return result