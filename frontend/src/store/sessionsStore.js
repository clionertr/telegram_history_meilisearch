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
      // 假设API返回的数据结构是 { items: [...], total: ... } 或者直接是数组
      // 我们需要根据实际返回调整
      // 如果API直接返回数组，并且没有总数，我们需要另一种方式处理 totalSessions 和 totalPages
      // 暂时假设API直接返回会话数组，并且我们需要在前端计算分页（如果后端不直接提供总数）
      // 或者，如果后端 get_dialogs_info 返回的是包含总数和当前页数据的对象，则更好
      
      // 临时处理：假设 getDialogs 直接返回会话数组
      // 并且我们暂时无法从后端获取 totalSessions
      // 后续需要改进后端API以返回总数
      
      // 更新：根据 user_bot/client.py 的 get_dialogs_info 返回的是 list[dict]
      // 这意味着我们无法直接从这个API获取总会话数。
      // 为了实现完整的分页，后端API需要调整以返回总数。
      // 目前，我们将只加载当前页的数据，分页控件可能不准确。
      
      set({
        sessions: data, // 直接使用返回的数据
        isLoading: false,
        currentPage: currentPageToFetch,
        // totalSessions: data.total, // 如果API返回总数
        // totalPages: Math.ceil(data.total / itemsPerPage), // 如果API返回总数
      });
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
      set({ error: error.message || '获取会话列表失败', isLoading: false });
    }
  },

  // 设置当前页
  setCurrentPage: (page) => {
    if (page > 0 && page <= get().totalPages) { // 确保页码有效 (如果totalPages已知)
      set({ currentPage: page });
      get().fetchSessions(page); // 切换页面时重新获取数据
    } else if (page > 0) { // 如果totalPages未知，允许设置并获取
        set({ currentPage: page });
        get().fetchSessions(page);
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