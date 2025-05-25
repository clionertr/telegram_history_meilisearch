/**
 * 导航状态管理 - 使用Zustand管理导航状态
 */
import { create } from 'zustand';

/**
 * 导航状态存储
 */
const useNavStore = create((set) => ({
  // 当前选中的导航项 (search, groups, settings)
  activeNav: 'search', // 默认选中搜索页面
  
  // 记录上次的导航状态，用于恢复
  prevActiveNav: null,
  
  // Actions
  
  /**
   * 设置当前活动的导航项
   * @param {string} nav - 导航项标识 (search, groups, settings)
   */
  setActiveNav: (nav) => set((state) => ({ 
    activeNav: nav,
    prevActiveNav: state.activeNav
  })),
  
  /**
   * 恢复到上一个导航项
   * 如果没有上一个导航项，则恢复到默认的搜索页
   */
  restorePrevNav: () => set((state) => ({
    activeNav: state.prevActiveNav || 'search',
    prevActiveNav: null
  }))
}));

export default useNavStore;