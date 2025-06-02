import { create } from 'zustand';
import { getDialogs } from '../services/api'; // 引入API调用函数

const useSessionsStore = create((set, get) => ({
  sessions: [], // 会话列表
  isLoading: false, // 加载状态
  error: null, // 错误状态
  
  // 分页状态
  currentPage: 1,
  itemsPerPage: 20, // 与后端API的limit一致
  totalSessions: 0, // 总会话数，用于计算总页数
  totalPages: 0,

  // 获取会话列表的异步action
  fetchSessions: async (page) => {
    set({ isLoading: true, error: null });
    const currentPageToFetch = page || get().currentPage;
    const itemsPerPage = get().itemsPerPage;

    try {
      const data = await getDialogs(currentPageToFetch, itemsPerPage);
      
      // 后端现在返回包含分页信息的对象：
      // { items: [...], total: ..., page: ..., limit: ..., total_pages: ... }
      if (data && typeof data === 'object' && Array.isArray(data.items)) {
        set({
          sessions: data.items,
          isLoading: false,
          currentPage: data.page || currentPageToFetch,
          totalSessions: data.total || 0,
          totalPages: data.total_pages || 0,
        });
      } else {
        // 兼容旧格式（直接返回数组）
        set({
          sessions: Array.isArray(data) ? data : [],
          isLoading: false,
          currentPage: currentPageToFetch,
          totalSessions: Array.isArray(data) ? data.length : 0,
          totalPages: 1,
        });
      }
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
      set({ error: error.message || '获取会话列表失败', isLoading: false });
    }
  },

  // 设置当前页
  setCurrentPage: (page) => {
    const { totalPages } = get();
    if (page > 0 && (totalPages === 0 || page <= totalPages)) { // 确保页码有效
      set({ currentPage: page });
      get().fetchSessions(page); // 切换页面时重新获取数据
    }
  },
  
  // (可选) 设置每页项目数
  setItemsPerPage: (count) => {
    set({ itemsPerPage: count, currentPage: 1 }); // 修改每页数量时重置到第一页
    get().fetchSessions(1); // 并重新获取数据
  },

  // (可选) 刷新会话列表
  refreshSessions: () => {
    get().fetchSessions(get().currentPage);
  },
}));

export default useSessionsStore;