import { create } from 'zustand';
import { getDialogs } from '../services/api'; // 引入API调用函数

const useSessionsStore = create((set, get) => ({
  sessions: [], // 会话列表
  isLoading: false, // 加载状态
  isLoadingAvatars: false, // 头像加载状态
  error: null, // 错误状态
  
  // 分页状态
  currentPage: 1,
  itemsPerPage: 20, // 与后端API的limit一致
  totalSessions: 0, // 总会话数，用于计算总页数
  totalPages: 0,

  // 获取会话列表的异步action（快速模式，不含头像）
  fetchSessionsFast: async (page) => {
    set({ isLoading: true, error: null });
    const currentPageToFetch = page || get().currentPage;
    const itemsPerPage = get().itemsPerPage;

    try {
      // 快速加载，不包含头像
      const data = await getDialogs(currentPageToFetch, itemsPerPage, false);
      
      if (data && typeof data === 'object' && Array.isArray(data.items)) {
        set({
          sessions: data.items,
          isLoading: false,
          currentPage: data.page || currentPageToFetch,
          totalSessions: data.total || 0,
          totalPages: data.total_pages || 0,
        });
        
        // 快速加载完成后，异步加载头像
        if (data.items.length > 0) {
          get().loadAvatarsForCurrentPage();
        }
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
      console.error("Fast fetch sessions failed:", error);
      set({ error: error.message || '获取会话列表失败', isLoading: false });
    }
  },

  // 获取会话列表的异步action（完整模式，包含头像）
  fetchSessions: async (page) => {
    set({ isLoading: true, error: null });
    const currentPageToFetch = page || get().currentPage;
    const itemsPerPage = get().itemsPerPage;

    try {
      const data = await getDialogs(currentPageToFetch, itemsPerPage, true);
      
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

  // 为当前页面的会话异步加载头像
  loadAvatarsForCurrentPage: async () => {
    const { currentPage, itemsPerPage, sessions } = get();
    
    if (sessions.length === 0) return;
    
    set({ isLoadingAvatars: true });
    
    try {
      // 获取包含头像的会话数据
      const data = await getDialogs(currentPage, itemsPerPage, true);
      
      if (data && typeof data === 'object' && Array.isArray(data.items)) {
        // 更新现有会话的头像数据
        const updatedSessions = sessions.map(session => {
          const sessionWithAvatar = data.items.find(item => item.id === session.id);
          if (sessionWithAvatar && sessionWithAvatar.avatar_base64) {
            return {
              ...session,
              avatar_base64: sessionWithAvatar.avatar_base64
            };
          }
          return session;
        });
        
        set({
          sessions: updatedSessions,
          isLoadingAvatars: false,
        });
      }
    } catch (error) {
      console.error("Failed to load avatars:", error);
      set({ isLoadingAvatars: false });
      // 头像加载失败不影响主要功能，不设置error
    }
  },

  // 设置当前页
  setCurrentPage: (page) => {
    const { totalPages } = get();
    if (page > 0 && (totalPages === 0 || page <= totalPages)) { // 确保页码有效
      set({ currentPage: page });
      get().fetchSessionsFast(page); // 切换页面时使用快速加载
    }
  },
  
  // (可选) 设置每页项目数
  setItemsPerPage: (count) => {
    set({ itemsPerPage: count, currentPage: 1 }); // 修改每页数量时重置到第一页
    get().fetchSessionsFast(1); // 并重新获取数据（快速模式）
  },

  // (可选) 刷新会话列表
  refreshSessions: () => {
    get().fetchSessionsFast(get().currentPage);
  },

  // 刷新会话列表（完整模式）
  refreshSessionsWithAvatars: () => {
    get().fetchSessions(get().currentPage);
  },
}));

export default useSessionsStore;