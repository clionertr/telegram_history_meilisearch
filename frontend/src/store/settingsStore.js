/**
 * 设置状态管理 - 使用Zustand管理设置状态
 */
import { create } from 'zustand';

/**
 * 设置状态存储
 */
const useSettingsStore = create((set) => ({
  // 外观设置
  appearance: {
    theme: 'auto', // 'light', 'dark', 'auto'(跟随系统)
  },
  
  // 同步设置
  sync: {
    frequency: 'daily', // 'hourly', 'daily', 'manual'
    lastSyncTime: null, // 上次同步时间，初始为null
    lastSyncStatus: null, // 'success', 'failed', null
    historyRange: 'last30days', // 'last7days', 'last30days', 'last90days', 'all'
  },
  
  // 缓存设置
  cache: {
    expirationDays: 7, // 缓存有效期（天）
    maxStorage: 100, // 最大缓存空间（MB）
  },
  
  // 通知设置
  notifications: {
    enabled: true, // 总开关
    syncComplete: true, // 同步完成通知
    newFeatures: true, // 新功能提醒
    sound: true, // 声音
    vibration: true, // 震动
  },

  // 白名单状态
  whitelist: {
    items: [], // 白名单项目
    isLoaded: false, // 是否已加载
  },
  
  // Actions
  
  /**
   * 设置主题
   * @param {string} theme - 'light', 'dark', 'auto'
   */
  setTheme: (theme) => set((state) => ({
    appearance: {
      ...state.appearance,
      theme
    }
  })),
  
  /**
   * 设置同步频率
   * @param {string} frequency - 'hourly', 'daily', 'manual'
   */
  setSyncFrequency: (frequency) => set((state) => ({
    sync: {
      ...state.sync,
      frequency
    }
  })),
  
  /**
   * 设置历史数据范围
   * @param {string} historyRange - 'last7days', 'last30days', 'last90days', 'all'
   */
  setHistoryRange: (historyRange) => set((state) => ({
    sync: {
      ...state.sync,
      historyRange
    }
  })),
  
  /**
   * 更新同步状态
   * @param {Object} syncInfo - 包含同步时间和状态的对象
   */
  updateSyncStatus: (syncInfo) => set((state) => ({
    sync: {
      ...state.sync,
      lastSyncTime: syncInfo.time || state.sync.lastSyncTime,
      lastSyncStatus: syncInfo.status || state.sync.lastSyncStatus
    }
  })),
  
  /**
   * 设置缓存有效期
   * @param {number} days - 缓存有效期（天）
   */
  setCacheExpiration: (days) => set((state) => ({
    cache: {
      ...state.cache,
      expirationDays: days
    }
  })),
  
  /**
   * 设置最大缓存空间
   * @param {number} size - 最大缓存空间（MB）
   */
  setMaxCacheStorage: (size) => set((state) => ({
    cache: {
      ...state.cache,
      maxStorage: size
    }
  })),
  
  /**
   * 清除缓存
   * 实际清除操作需要与API交互，这里只提供状态更新
   * @returns {Promise} 表示清除操作的Promise
   */
  clearCache: async () => {
    // TODO: 实现与后端API的缓存清除交互
    // 临时实现，返回成功的Promise
    return Promise.resolve({ success: true, message: '缓存已清除' });
  },
  
  /**
   * 设置通知总开关
   * @param {boolean} enabled - 是否启用通知
   */
  setNotificationsEnabled: (enabled) => set((state) => ({
    notifications: {
      ...state.notifications,
      enabled
    }
  })),
  
  /**
   * 设置特定通知类型的开关
   * @param {string} type - 通知类型 ('syncComplete', 'newFeatures')
   * @param {boolean} enabled - 是否启用此类通知
   */
  setNotificationType: (type, enabled) => set((state) => ({
    notifications: {
      ...state.notifications,
      [type]: enabled
    }
  })),
  
  /**
   * 加载白名单
   * 实际操作需要与API交互，这里只提供状态更新
   */
  loadWhitelist: async () => {
    // TODO: 实现与后端API的白名单加载交互
    // 临时实现，返回模拟数据
    const mockData = [
      { id: 1, value: 'example.com' },
      { id: 2, value: '192.168.1.1' },
    ];
    
    set({
      whitelist: {
        items: mockData,
        isLoaded: true
      }
    });
    
    return mockData;
  },
}));

export default useSettingsStore;