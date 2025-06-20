import React from 'react';
import { getDialogs, searchDialogs, getCacheStatus, refreshCache, clearAvatarsCache } from '../services/api.js';

// 事件监听器管理
class EventEmitter {
  constructor() {
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    
    // 返回取消订阅函数
    return () => {
      const eventListeners = this.listeners.get(event);
      if (eventListeners) {
        eventListeners.delete(callback);
      }
    };
  }

  emit(event, data) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => callback(data));
    }
  }
}

// 创建状态管理器
class SessionsStore extends EventEmitter {
  constructor() {
    super();
    
    // 基础状态
    this.state = {
      sessions: [],
      totalSessions: 0,
      currentPage: 1,
      totalPages: 0,
      pageSize: 20,
      isLoading: false,
      isLoadingAvatars: false,
      error: null,
      cacheStatus: {
        cached_dialogs_count: 0,
        cached_avatars_count: 0,
        cache_valid: false,
        cache_age_seconds: null,
        cache_ttl_seconds: 300
      },
      // 搜索相关状态
      searchQuery: '',
      searchTypeFilter: '',
      isSearchMode: false,
      searchResults: [],
      isSearching: false,
      searchError: null
    };

    // 全局会话缓存
    this.allSessionsCache = [];
    this.cacheTimestamp = null;
    this.isCacheInitialized = false;
  }

  // 获取当前状态
  getState() {
    return { ...this.state };
  }

  // 更新状态并触发事件
  setState(updates) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...updates };
    
    // 触发相关事件
    Object.keys(updates).forEach(key => {
      this.emit(key, this.state[key]);
    });
    
    this.emit('stateChange', this.state);
  }

  // 清除错误状态
  clearError() {
    this.setState({ error: null, searchError: null });
  }

  // 清除搜索错误
  clearSearchError() {
    this.setState({ searchError: null });
  }

  // 获取缓存状态
  async fetchCacheStatus() {
    try {
      const status = await getCacheStatus();
      this.setState({ cacheStatus: status });
      return status;
    } catch (err) {
      console.error('获取缓存状态失败:', err);
      return null;
    }
  }

  // 获取所有会话并缓存
  async fetchSessions(page = 1, forceRefresh = false) {
    try {
      this.clearError();
      
      // 如果缓存已初始化且不强制刷新，直接切换页面
      if (this.isCacheInitialized && !forceRefresh) {
        await this.changePage(page);
        return;
      }

      this.setState({ isLoading: true });
      
      // 分批获取所有数据
      console.log('开始分批获取会话数据...');
      let allSessions = [];
      let currentPage = 1;
      let totalCount = 0;
      
      // 先获取第一页来了解总数
      const firstPageResult = await getDialogs(1, 100, true);
      if (!firstPageResult || !firstPageResult.items) {
        throw new Error('获取会话数据失败');
      }
      
      allSessions = [...firstPageResult.items];
      totalCount = firstPageResult.total;
      const totalPages = Math.ceil(totalCount / 100);
      
      console.log(`总共需要获取 ${totalPages} 页，总计 ${totalCount} 个会话`);
      
      // 获取剩余页面
      const pagePromises = [];
      for (let pageNum = 2; pageNum <= Math.min(totalPages, 10); pageNum++) { // 最多获取10页，避免过度请求
        pagePromises.push(getDialogs(pageNum, 100, true));
      }
      
      if (pagePromises.length > 0) {
        const results = await Promise.all(pagePromises);
        results.forEach(result => {
          if (result && result.items) {
            allSessions = [...allSessions, ...result.items];
          }
        });
      }
      
      // 缓存所有会话数据
      this.allSessionsCache = allSessions;
      this.cacheTimestamp = Date.now();
      this.isCacheInitialized = true;
      
      // 更新状态
      const calculatedTotalPages = Math.ceil(totalCount / this.state.pageSize);
      this.setState({
        totalSessions: totalCount,
        totalPages: calculatedTotalPages,
        currentPage: page
      });
      
      // 更新当前页数据
      this.updateCurrentPageSessions();
      
      console.log(`缓存已初始化: ${this.allSessionsCache.length} 个会话`);
      
      // 现在头像已在后端启动时预下载，无需额外加载
      
    } catch (err) {
      console.error('获取会话数据失败:', err);
      this.setState({ error: err.message || '获取会话数据失败' });
    } finally {
      this.setState({ isLoading: false });
    }
  }

  // 更新当前页的会话数据
  updateCurrentPageSessions() {
    const { currentPage, pageSize } = this.state;
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const pageData = this.allSessionsCache.slice(startIndex, endIndex);
    
    this.setState({ sessions: pageData });
  }

  // 快速切换页面（无API调用）
  async changePage(page) {
    if (!this.isCacheInitialized) {
      // 如果缓存未初始化，执行完整加载
      await this.fetchSessions(page);
      return;
    }
    
    const { pageSize, totalSessions } = this.state;
    const calculatedTotalPages = Math.ceil(totalSessions / pageSize);
    
    if (page < 1 || page > calculatedTotalPages) {
      console.warn(`页码 ${page} 超出范围 [1, ${calculatedTotalPages}]`);
      return;
    }
    
    // 立即更新页码和数据
    this.setState({ currentPage: page });
    this.updateCurrentPageSessions();
    
    console.log(`瞬时切换到第 ${page} 页`);
    
    // 头像已在后端预下载，无需额外加载
  }

  // 手动刷新缓存
  async refreshSessionsCache() {
    try {
      this.setState({ isLoading: true });
      this.clearError();
      
      console.log('手动刷新会话缓存...');
      
      // 调用后端刷新缓存API
      await refreshCache();
      
      // 清除前端缓存
      this.allSessionsCache = [];
      this.isCacheInitialized = false;
      this.cacheTimestamp = null;
      
      // 重新获取数据
      await this.fetchSessions(1, true);
      
      console.log('缓存刷新完成');
    } catch (err) {
      console.error('刷新缓存失败:', err);
      this.setState({ error: err.message || '刷新缓存失败' });
    } finally {
      this.setState({ isLoading: false });
    }
  }

  // 清除头像缓存
  async clearAvatarCache() {
    try {
      console.log('清除头像缓存...');
      
      // 调用后端清除头像缓存API
      await clearAvatarsCache();
      
      // 清除前端缓存中的头像数据
      this.allSessionsCache = this.allSessionsCache.map(session => ({
        ...session,
        avatar_base64: null
      }));
      
      // 更新当前显示的数据
      this.updateCurrentPageSessions();
      
      console.log('头像缓存已清除');
      
      // 头像将在后端下次预下载时重新获取
    } catch (err) {
      console.error('清除头像缓存失败:', err);
      this.setState({ error: err.message || '清除头像缓存失败' });
    }
  }

  // 搜索会话
  async searchSessions(query, typeFilter = '', page = 1) {
    try {
      this.clearSearchError();
      
      // 如果查询为空，退出搜索模式
      if (!query || query.trim() === '') {
        this.exitSearchMode();
        return;
      }

      this.setState({ 
        isSearching: true,
        searchQuery: query.trim(),
        searchTypeFilter: typeFilter,
        isSearchMode: true
      });

      console.log(`搜索会话: "${query}", 类型过滤: "${typeFilter}", 页码: ${page}`);

      const searchResults = await searchDialogs(query.trim(), page, this.state.pageSize, typeFilter || null);
      
      if (!searchResults) {
        throw new Error('搜索返回空结果');
      }

      // 更新搜索结果
      this.setState({
        searchResults: searchResults.items || [],
        sessions: searchResults.items || [], // 当前显示的会话列表
        totalSessions: searchResults.total || 0,
        currentPage: searchResults.page || page,
        totalPages: searchResults.total_pages || 0
      });

      console.log(`搜索完成: 找到 ${searchResults.total || 0} 个结果`);

    } catch (err) {
      console.error('搜索会话失败:', err);
      this.setState({ 
        searchError: err.message || '搜索失败',
        searchResults: [],
        sessions: [],
        totalSessions: 0,
        totalPages: 0
      });
    } finally {
      this.setState({ isSearching: false });
    }
  }

  // 搜索模式下的分页
  async searchChangePage(page) {
    if (!this.state.isSearchMode || !this.state.searchQuery) {
      return;
    }

    await this.searchSessions(this.state.searchQuery, this.state.searchTypeFilter, page);
  }

  // 退出搜索模式
  exitSearchMode() {
    this.setState({
      isSearchMode: false,
      searchQuery: '',
      searchTypeFilter: '',
      searchResults: [],
      searchError: null
    });

    // 恢复到正常浏览模式
    if (this.isCacheInitialized) {
      this.updateCurrentPageSessions();
    } else {
      // 如果缓存未初始化，重新加载
      this.fetchSessions(1);
    }
  }

  // 设置类型过滤器
  setTypeFilter(typeFilter) {
    if (this.state.isSearchMode && this.state.searchQuery) {
      // 在搜索模式下，重新搜索
      this.searchSessions(this.state.searchQuery, typeFilter, 1);
    } else {
      // 在普通模式下，只更新状态
      this.setState({ searchTypeFilter: typeFilter });
    }
  }

  // 获取搜索建议（这里可以扩展为实际的搜索建议功能）
  getSearchSuggestions(query) {
    if (!query || query.length < 2) {
      return [];
    }

    // 从缓存的会话中获取匹配的建议
    const suggestions = this.allSessionsCache
      .filter(session => 
        session.name && session.name.toLowerCase().includes(query.toLowerCase())
      )
      .slice(0, 5) // 最多5个建议
      .map(session => session.name);

    return [...new Set(suggestions)]; // 去重
  }

  // 获取缓存统计信息
  getCacheInfo() {
    return {
      isCacheInitialized: this.isCacheInitialized,
      cacheSize: this.allSessionsCache.length,
      cacheTimestamp: this.cacheTimestamp,
      cacheAge: this.cacheTimestamp ? Date.now() - this.cacheTimestamp : null
    };
  }

  // 兼容性：保持原有的快速加载方法
  async fetchSessionsFast(page = 1) {
    await this.fetchSessions(page, false);
  }
}

// 创建全局store实例
const sessionsStore = new SessionsStore();

// 导出store和相关方法
export default sessionsStore;

// 导出便利方法
export const {
  getState,
  setState,
  clearError,
  clearSearchError,
  fetchCacheStatus,
  fetchSessions,
  changePage,
  refreshSessionsCache,
  clearAvatarCache,
  getCacheInfo,
  fetchSessionsFast,
  searchSessions,
  searchChangePage,
  exitSearchMode,
  setTypeFilter,
  getSearchSuggestions
} = sessionsStore;

// 创建React Hook
export const useSessionsStore = () => {
  const [state, setState] = React.useState(sessionsStore.getState());

  React.useEffect(() => {
    const unsubscribe = sessionsStore.on('stateChange', setState);
    return unsubscribe;
  }, []);

  return {
    ...state,
    fetchSessions: sessionsStore.fetchSessions.bind(sessionsStore),
    changePage: sessionsStore.changePage.bind(sessionsStore),
    refreshSessionsCache: sessionsStore.refreshSessionsCache.bind(sessionsStore),
    clearAvatarCache: sessionsStore.clearAvatarCache.bind(sessionsStore),
    fetchCacheStatus: sessionsStore.fetchCacheStatus.bind(sessionsStore),
    getCacheInfo: sessionsStore.getCacheInfo.bind(sessionsStore),
    fetchSessionsFast: sessionsStore.fetchSessionsFast.bind(sessionsStore),
    // 搜索相关方法
    searchSessions: sessionsStore.searchSessions.bind(sessionsStore),
    searchChangePage: sessionsStore.searchChangePage.bind(sessionsStore),
    exitSearchMode: sessionsStore.exitSearchMode.bind(sessionsStore),
    setTypeFilter: sessionsStore.setTypeFilter.bind(sessionsStore),
    getSearchSuggestions: sessionsStore.getSearchSuggestions.bind(sessionsStore),
    clearSearchError: sessionsStore.clearSearchError.bind(sessionsStore)
  };
};