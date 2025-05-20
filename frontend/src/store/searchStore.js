/**
 * 搜索状态管理 - 使用Zustand管理搜索状态
 */
import { create } from 'zustand';
import { searchMessages } from '../services/api';

/**
 * 搜索状态存储
 */
const useSearchStore = create((set, get) => ({
  // 基础状态
  query: '',           // 当前搜索关键词
  results: [],         // 搜索结果列表
  isLoading: false,    // 加载状态
  error: null,         // 错误信息

  // 分页信息
  pagination: {
    currentPage: 1,    // 当前页码
    totalPages: 0,     // 总页数
    totalHits: 0,      // 总结果数
    hitsPerPage: 10,   // 每页结果数
  },

  // 筛选条件
  filters: {
    chat_type: [],     // 聊天类型数组，可选值: "user", "group", "channel"
    date_from: null,   // 起始日期时间戳
    date_to: null,     // 结束日期时间戳
  },

  // Actions

  /**
   * 设置搜索关键词
   * @param {string} query - 搜索关键词
   */
  setQuery: (query) => set({ query }),

  /**
   * 设置筛选条件
   * @param {Object} filters - 新的筛选条件
   */
  setFilters: (filters) => set({ 
    filters: { ...get().filters, ...filters } 
  }),

  /**
   * 设置当前页码
   * @param {number} page - 页码
   */
  setPage: (page) => set(state => ({
    pagination: { ...state.pagination, currentPage: page }
  })),

  /**
   * 设置每页结果数量
   * @param {number} hitsPerPage - 每页结果数量
   */
  setHitsPerPage: (hitsPerPage) => set(state => ({
    pagination: { ...state.pagination, hitsPerPage }
  })),

  /**
   * 清空搜索结果
   */
  clearResults: () => set({
    results: [],
    error: null,
    pagination: {
      ...get().pagination,
      totalHits: 0,
      totalPages: 0,
    }
  }),

  /**
   * 执行搜索
   * 如果不提供参数，则使用store中的当前状态
   * @param {string} [query] - 搜索关键词，不传则使用当前store中的query
   * @param {number} [page] - 页码，不传则使用当前store中的page
   * @param {number} [hitsPerPage] - 每页结果数量，不传则使用当前store中的hitsPerPage
   * @param {Object} [filters] - 过滤条件，不传则使用当前store中的filters
   */
  fetchResults: async (query, page, hitsPerPage, filters) => {
    // 使用传入的参数或从store获取当前值
    const searchQuery = query || get().query;
    const searchPage = page || get().pagination.currentPage;
    const searchHitsPerPage = hitsPerPage || get().pagination.hitsPerPage;
    const searchFilters = filters || get().filters;

    // 检查搜索词是否为空
    if (!searchQuery.trim()) {
      set({ error: '请输入搜索关键词' });
      return;
    }

    // 设置加载状态
    set({ isLoading: true, error: null });

    try {
      // 调用API进行搜索
      const response = await searchMessages(
        searchQuery, 
        searchFilters, 
        searchPage, 
        searchHitsPerPage
      );

      // 计算总页数
      const totalPages = Math.ceil(response.estimatedTotalHits / searchHitsPerPage) || 0;

      // 更新状态
      set({
        results: response.hits || [],
        isLoading: false,
        pagination: {
          currentPage: searchPage,
          totalPages,
          totalHits: response.estimatedTotalHits || 0,
          hitsPerPage: searchHitsPerPage,
        }
      });
    } catch (error) {
      // 处理错误
      set({
        isLoading: false,
        error: error.message || '搜索请求失败',
        results: [],
      });
    }
  }
}));

export default useSearchStore;