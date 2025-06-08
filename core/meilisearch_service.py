"""
Meilisearch 服务模块

此模块提供与 Meilisearch 交互的功能，包括：
1. 初始化 Meilisearch 客户端
2. 配置索引设置
3. 索引消息（单条或批量）
4. 搜索消息
5. 删除消息（可选）
6. 会话索引与搜索功能
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
    支持会话索引与搜索功能
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
        self.sessions_index_name = "telegram_sessions"  # 会话索引名称
        
        # 初始化 Meilisearch 客户端
        self.client = meilisearch.Client(self.host, self.api_key)
        self.logger.info(f"已连接到 Meilisearch 服务: {self.host}")
        
        # 获取或创建消息索引
        self.index = self.client.index(self.index_name)
        self.logger.info(f"使用消息索引: {self.index_name}")
        
        # 获取或创建会话索引
        self.sessions_index = self.client.index(self.sessions_index_name)
        self.logger.info(f"使用会话索引: {self.sessions_index_name}")
        
        # 确保索引设置正确
        self.ensure_index_setup()
        self.ensure_sessions_index_setup()
    
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
            # 显式指定 id 字段为主键
            self.client.create_index(self.index_name, {'primaryKey': 'id'})
            self.logger.info(f"已指定 'id' 为索引的主键")
        else:
            # 确保已有索引的主键设置正确
            try:
                index_info = self.client.get_index(self.index_name)
                if not hasattr(index_info, 'primary_key') or index_info.primary_key != 'id':
                    self.logger.warning(f"索引 {self.index_name} 的主键不是 'id'，尝试更新")
                    # 注意：有些版本的 Meilisearch 不允许修改已有索引的主键
                    # 此处可能需要删除并重建索引
                    pass
            except Exception as e:
                self.logger.warning(f"检查索引主键时出错: {str(e)}")
        
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
        
        # 配置高亮属性
        self.index.update_displayed_attributes([
            "id",
            "message_id",
            "chat_id",
            "chat_title",
            "chat_type",
            "sender_id",
            "sender_name",
            "text",
            "date",
            "message_link"
        ])
        self.logger.info("已配置显示属性")
        
        # 日志记录关于停用词和同义词
        self.logger.info("注意: stopWords(停用词)和synonyms(同义词)配置不在初始设置中，可通过单独的方法配置")
    
    def ensure_sessions_index_setup(self) -> None:
        """
        确保会话索引存在并配置正确
        
        配置会话索引的可搜索属性、可过滤属性、可排序属性和排序规则。
        """
        # 获取所有索引
        indexes = self.client.get_indexes()
        
        # 兼容不同版本 Meilisearch API 的返回结构
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
        
        # 检查是否需要创建会话索引
        if self.sessions_index_name not in index_names:
            self.logger.info(f"会话索引 {self.sessions_index_name} 不存在，正在创建...")
            # 显式指定 id 字段为主键
            self.client.create_index(self.sessions_index_name, {'primaryKey': 'id'})
            self.logger.info(f"已指定 'id' 为会话索引的主键")
        else:
            # 确保已有索引的主键设置正确
            try:
                index_info = self.client.get_index(self.sessions_index_name)
                if not hasattr(index_info, 'primary_key') or index_info.primary_key != 'id':
                    self.logger.warning(f"会话索引 {self.sessions_index_name} 的主键不是 'id'，尝试更新")
            except Exception as e:
                self.logger.warning(f"检查会话索引主键时出错: {str(e)}")
        
        # 配置会话索引设置
        # 可搜索属性 - name 优先级最高
        self.sessions_index.update_searchable_attributes([
            "name",
            "id"
        ])
        self.logger.info("已配置会话索引可搜索属性: ['name', 'id']")
        
        # 可过滤属性
        self.sessions_index.update_filterable_attributes([
            "type",
            "unread_count"
        ])
        self.logger.info("已配置会话索引可过滤属性: ['type', 'unread_count']")
        
        # 可排序属性
        self.sessions_index.update_sortable_attributes([
            "date",
            "unread_count",
            "name"
        ])
        self.logger.info("已配置会话索引可排序属性: ['date', 'unread_count', 'name']")
        
        # 排序规则
        self.sessions_index.update_ranking_rules([
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness"
        ])
        self.logger.info("已配置会话索引排序规则")
        
        # 配置高亮属性
        self.sessions_index.update_displayed_attributes([
            "id",
            "name",
            "type",
            "unread_count",
            "date",
            "avatar_key"
        ])
        self.logger.info("已配置会话索引显示属性")
    
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
        
        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            # 兼容旧版 API
            task_id = result['taskUid']
            
        self.logger.debug(f"已索引消息: {message_doc.id}, 任务ID: {task_id}")
        
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

        # 提取会话ID和消息ID范围信息用于日志记录
        chat_ids = set()
        message_ids = []

        for doc in message_docs:
            chat_ids.add(doc.chat_id)
            message_ids.append(doc.message_id)

        # 计算消息ID范围
        min_message_id = min(message_ids) if message_ids else 0
        max_message_id = max(message_ids) if message_ids else 0

        # 格式化会话ID信息
        if len(chat_ids) == 1:
            session_info = f"会话ID: {list(chat_ids)[0]}"
        else:
            session_info = f"会话ID: {sorted(chat_ids)} ({len(chat_ids)}个会话)"

        # 将所有 Pydantic 模型转换为字典列表
        docs_dict = [doc.model_dump() for doc in message_docs]

        # 批量添加到 Meilisearch 索引
        result = self.index.add_documents(docs_dict)

        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            # 兼容旧版 API
            task_id = result['taskUid']

        self.logger.info(f"已批量索引 {len(message_docs)} 条消息，{session_info}，消息ID范围: {min_message_id}-{max_message_id}，任务ID: {task_id}")

        return result
    
    def search(self, query: str, filters: Optional[str] = None, sort: Optional[List[str]] = None,
               page: int = 1, hits_per_page: int = 10,
               start_timestamp: Optional[int] = None, end_timestamp: Optional[int] = None,
               chat_types: Optional[List[str]] = None, chat_ids: Optional[List[int]] = None) -> dict:
        """
        搜索消息
        
        Args:
            query: 搜索关键词
            filters: Meilisearch 过滤字符串，例如 "chat_id = 12345 AND date > 1672531200"
            sort: 排序规则列表，例如 ["date:desc"]
            page: 页码，从 1 开始
            hits_per_page: 每页结果数
            start_timestamp: 开始时间的 Unix 时间戳
            end_timestamp: 结束时间的 Unix 时间戳
            chat_types: 聊天类型列表，例如 ["group", "channel", "user"]
            chat_ids: 聊天 ID 列表，例如 [12345, 67890]
            
        Returns:
            Meilisearch 的搜索结果字典
        """
        # 构建过滤条件
        filter_parts = []
        
        # 处理传入的 filters 参数
        if filters:
            filter_parts.append(f"({filters})")
        
        # 处理时间范围过滤
        if start_timestamp is not None:
            filter_parts.append(f"date >= {start_timestamp}")
        if end_timestamp is not None:
            filter_parts.append(f"date <= {end_timestamp}")
        
        # 处理聊天类型过滤
        if chat_types:
            # 验证聊天类型的有效性
            valid_chat_types = {"user", "group", "channel"}
            invalid_types = [t for t in chat_types if t not in valid_chat_types]
            if invalid_types:
                self.logger.warning(f"发现无效的聊天类型: {invalid_types}, 有效类型: {list(valid_chat_types)}")
            
            valid_types = [t for t in chat_types if t in valid_chat_types]
            if valid_types:
                chat_type_filters = [f'chat_type = "{chat_type}"' for chat_type in valid_types]
                filter_parts.append(f"({' OR '.join(chat_type_filters)})")
        
        # 处理聊天ID过滤
        if chat_ids:
            # 确保所有ID都是整数
            valid_chat_ids = []
            for chat_id in chat_ids:
                if isinstance(chat_id, int):
                    valid_chat_ids.append(chat_id)
                else:
                    self.logger.warning(f"聊天ID必须是整数，忽略: {chat_id}")
            
            if valid_chat_ids:
                chat_id_filters = [f"chat_id = {chat_id}" for chat_id in valid_chat_ids]
                filter_parts.append(f"({' OR '.join(chat_id_filters)})")
        
        # 构建搜索参数
        search_params: Dict[str, Any] = {
            "page": page,
            "hitsPerPage": hits_per_page,
            "attributesToHighlight": ["text"]
        }
        
        # 添加组合后的过滤条件
        if filter_parts:
            combined_filters = " AND ".join(filter_parts)
            search_params["filter"] = combined_filters
            self.logger.debug(f"组合过滤条件: {combined_filters}")
        
        # 添加排序规则（默认按日期降序）
        if sort:
            search_params["sort"] = sort
        else:
            search_params["sort"] = ["date:desc"]
        
        # 执行搜索
        self.logger.debug(f"执行搜索: 关键词='{query}', 参数={search_params}")
        self.logger.debug(f"高级过滤参数: start_timestamp={start_timestamp}, end_timestamp={end_timestamp}, "
                         f"chat_types={chat_types}, chat_ids={chat_ids}")
        results = self.index.search(query, search_params)
        
        # 记录原始搜索结果以便排查问题
        self.logger.debug(f"Meilisearch 原始搜索结果: {results}")
        
        # 处理不同版本 Meilisearch API 的返回结构
        # 确保结果包含必要的键，兼容新旧版 API
        # 标准化为字典格式
        if not isinstance(results, dict):
            # 如果返回的不是字典，尝试转换为字典
            # 可能是 SearchResponse 对象等
            self.logger.debug(f"搜索结果不是字典，类型: {type(results)}")
            if hasattr(results, '__dict__'):
                results_dict = dict(results.__dict__)
            else:
                # 尝试获取常见属性
                results_dict = {}
                for attr in ['hits', 'estimatedTotalHits', 'processingTimeMs', 'query']:
                    if hasattr(results, attr):
                        results_dict[attr] = getattr(results, attr)
        else:
            results_dict = results
        
        # 确保结果包含所有必要的键
        if 'hits' not in results_dict:
            results_dict['hits'] = []
        if 'estimatedTotalHits' not in results_dict:
            # 尝试从不同可能的属性名获取真实的总命中数
            # 按优先级顺序尝试不同的字段
            if hasattr(results, 'estimated_total_hits'):
                results_dict['estimatedTotalHits'] = results.estimated_total_hits
            elif hasattr(results, 'nb_hits'):
                results_dict['estimatedTotalHits'] = results.nb_hits
            # 尝试从totalHits字段获取
            elif hasattr(results, 'totalHits'):
                results_dict['estimatedTotalHits'] = results.totalHits
            elif 'totalHits' in results_dict:
                results_dict['estimatedTotalHits'] = results_dict['totalHits']
            # 如果有totalPages，根据totalPages和每页结果数计算
            elif hasattr(results, 'totalPages'):
                results_dict['estimatedTotalHits'] = results.totalPages * search_params['hitsPerPage']
            elif 'totalPages' in results_dict:
                results_dict['estimatedTotalHits'] = results_dict['totalPages'] * search_params['hitsPerPage']
            # 最后才回退到使用当前页的结果数量
            else:
                self.logger.warning("无法找到真实的总命中数，使用当前页结果数量作为估计值")
                results_dict['estimatedTotalHits'] = len(results_dict['hits'])
        
        if 'processingTimeMs' not in results_dict:
            # 尝试从不同可能的属性名获取
            if hasattr(results, 'processing_time_ms'):
                results_dict['processingTimeMs'] = results.processing_time_ms
            else:
                results_dict['processingTimeMs'] = 0
        
        if 'query' not in results_dict:
            results_dict['query'] = query
        
        # 记录搜索结果信息
        self.logger.info(
            f"搜索 '{query}' 找到 {results_dict['estimatedTotalHits']} 条结果，"
            f"处理时间: {results_dict['processingTimeMs']}ms，"
            f"每页限制: {search_params['hitsPerPage']}，"
            f"当前页码: {search_params['page']}，"
            f"实际返回结果数: {len(results_dict['hits'])}，"
            f"估计总结果数: {results_dict['estimatedTotalHits']}"
        )
        
        return results_dict
    
    def delete_message(self, document_id: str) -> dict:
        """
        删除单条消息
        
        Args:
            document_id: 文档ID，通常是 MeiliMessageDoc.id
            
        Returns:
            Meilisearch 的响应字典，通常包含任务信息
        """
        result = self.index.delete_document(document_id)
        
        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            # 兼容旧版 API
            task_id = result['taskUid']
            
        self.logger.info(f"已删除消息: {document_id}, 任务ID: {task_id}")
        
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
        
        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            # 兼容旧版 API
            task_id = result['taskUid']
            
        self.logger.info(f"已更新停用词列表，词数: {len(stop_words)}, 任务ID: {task_id}")
        
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
        
        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            # 兼容旧版 API
            task_id = result['taskUid']
            
        self.logger.info(f"已更新同义词词典，词组数: {len(synonyms)}, 任务ID: {task_id}")
        
        return result

    def index_session(self, session_doc: Dict[str, Any]) -> dict:
        """
        索引单个会话
        
        Args:
            session_doc: 会话文档字典，包含id, name, type, unread_count, date, avatar_key等字段
            
        Returns:
            Meilisearch 的响应字典，通常包含任务信息
        """
        # 添加到 Meilisearch 会话索引
        result = self.sessions_index.add_documents([session_doc])
        
        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            # 兼容旧版 API
            task_id = result['taskUid']
            
        self.logger.debug(f"已索引会话: {session_doc.get('id')}, 任务ID: {task_id}")
        
        return result

    def index_sessions_bulk(self, session_docs: List[Dict[str, Any]]) -> dict:
        """
        批量索引会话
        
        Args:
            session_docs: 会话文档列表
            
        Returns:
            Meilisearch 的响应字典，通常包含任务信息
        """
        if not session_docs:
            self.logger.warning("会话文档列表为空，跳过索引")
            return {}
        
        # 批量添加到 Meilisearch 会话索引
        result = self.sessions_index.add_documents(session_docs)
        
        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            # 兼容旧版 API
            task_id = result['taskUid']
            
        self.logger.info(f"已批量索引 {len(session_docs)} 个会话, 任务ID: {task_id}")
        
        return result

    def search_sessions(self, query: str, session_types: Optional[List[str]] = None, 
                       page: int = 1, hits_per_page: int = 20,
                       sort: Optional[List[str]] = None) -> dict:
        """
        搜索会话
        
        Args:
            query: 搜索关键词，支持搜索会话名称和ID
            session_types: 会话类型过滤，如 ["user", "group", "channel"]
            page: 页码，从1开始
            hits_per_page: 每页结果数，默认20
            sort: 排序规则，如 ["date:desc", "unread_count:desc"]
            
        Returns:
            搜索结果字典，包含hits、estimatedTotalHits等信息
        """
        filter_parts = []
        
        # 处理会话类型过滤
        if session_types:
            # 验证会话类型的有效性
            valid_session_types = {"user", "group", "channel"}
            invalid_types = [t for t in session_types if t not in valid_session_types]
            if invalid_types:
                self.logger.warning(f"发现无效的会话类型: {invalid_types}, 有效类型: {list(valid_session_types)}")
            
            valid_types = [t for t in session_types if t in valid_session_types]
            if valid_types:
                type_filters = [f'type = "{session_type}"' for session_type in valid_types]
                filter_parts.append(f"({' OR '.join(type_filters)})")
        
        # 构建搜索参数
        search_params: Dict[str, Any] = {
            "page": page,
            "hitsPerPage": hits_per_page,
            "attributesToHighlight": ["name"]
        }
        
        # 添加组合后的过滤条件
        if filter_parts:
            combined_filters = " AND ".join(filter_parts)
            search_params["filter"] = combined_filters
            self.logger.debug(f"会话搜索过滤条件: {combined_filters}")
        
        # 添加排序规则（默认按日期降序）
        if sort:
            search_params["sort"] = sort
        else:
            search_params["sort"] = ["date:desc"]
        
        # 执行搜索
        self.logger.debug(f"执行会话搜索: 关键词='{query}', 参数={search_params}")
        results = self.sessions_index.search(query, search_params)
        
        # 记录原始搜索结果以便排查问题
        self.logger.debug(f"Meilisearch 会话搜索原始结果: {results}")
        
        # 处理不同版本 Meilisearch API 的返回结构
        if not isinstance(results, dict):
            self.logger.debug(f"会话搜索结果不是字典，类型: {type(results)}")
            if hasattr(results, '__dict__'):
                results_dict = dict(results.__dict__)
            else:
                results_dict = {}
                for attr in ['hits', 'estimatedTotalHits', 'processingTimeMs', 'query']:
                    if hasattr(results, attr):
                        results_dict[attr] = getattr(results, attr)
        else:
            results_dict = results
        
        # 确保结果包含所有必要的键
        if 'hits' not in results_dict:
            results_dict['hits'] = []
        if 'estimatedTotalHits' not in results_dict:
            if hasattr(results, 'estimated_total_hits'):
                results_dict['estimatedTotalHits'] = results.estimated_total_hits
            elif hasattr(results, 'nb_hits'):
                results_dict['estimatedTotalHits'] = results.nb_hits
            elif hasattr(results, 'totalHits'):
                results_dict['estimatedTotalHits'] = results.totalHits
            elif 'totalHits' in results_dict:
                results_dict['estimatedTotalHits'] = results_dict['totalHits']
            else:
                results_dict['estimatedTotalHits'] = len(results_dict['hits'])
        
        if 'processingTimeMs' not in results_dict:
            if hasattr(results, 'processing_time_ms'):
                results_dict['processingTimeMs'] = results.processing_time_ms
            else:
                results_dict['processingTimeMs'] = 0
        
        if 'query' not in results_dict:
            results_dict['query'] = query
        
        # 记录会话搜索结果信息
        self.logger.info(
            f"会话搜索 '{query}' 找到 {results_dict['estimatedTotalHits']} 个结果，"
            f"处理时间: {results_dict['processingTimeMs']}ms，"
            f"当前页码: {search_params['page']}，"
            f"实际返回结果数: {len(results_dict['hits'])}"
        )
        
        return results_dict

    def clear_sessions_index(self) -> dict:
        """
        清空会话索引
        
        Returns:
            Meilisearch 的响应字典
        """
        result = self.sessions_index.delete_all_documents()
        
        # 适配新版 Meilisearch API 返回值处理
        task_id = "unknown"
        if hasattr(result, 'task_uid'):
            task_id = result.task_uid
        elif hasattr(result, 'uid'):
            task_id = result.uid
        elif isinstance(result, dict) and 'taskUid' in result:
            task_id = result['taskUid']
            
        self.logger.info(f"已清空会话索引，任务ID: {task_id}")
        
        return result