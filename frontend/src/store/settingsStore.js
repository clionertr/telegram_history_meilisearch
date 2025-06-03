/**
 * 设置状态管理 - 使用Zustand管理设置状态
 */
import { create } from 'zustand';
import {
  getWhitelist,
  addToWhitelist,
  removeFromWhitelist,
  getSyncSettings,
  setGlobalOldestSyncTimestamp,
  setChatOldestSyncTimestamp,
  getChatOldestSyncTimestamp
} from '../services/api';

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
    // 最旧同步时间管理
    oldestSyncSettings: {
      global: null, // 全局最旧同步时间戳
      chats: {}, // 特定聊天的最旧同步时间戳 {chatId: timestamp}
      isLoaded: false, // 是否已加载设置
    },
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
   * 加载同步设置
   * @param {boolean} forceRefresh - 是否强制刷新，忽略缓存状态
   * @returns {Promise} 加载操作的Promise
   */
  loadSyncSettings: async (forceRefresh = false) => {
    try {
      const response = await getSyncSettings();
      const syncSettings = response.sync_settings || {};

      // 解析聊天设置：后端格式是 {chatId: {oldest_sync_timestamp: "..."}}
      // 前端需要的格式是 {chatId: "timestamp"}
      const chats = {};
      Object.entries(syncSettings).forEach(([key, value]) => {
        // 跳过全局设置
        if (key === 'global_oldest_sync_timestamp') return;

        // 如果值是对象且包含 oldest_sync_timestamp，则提取时间戳
        if (value && typeof value === 'object' && value.oldest_sync_timestamp) {
          chats[key] = value.oldest_sync_timestamp;
        }
      });

      set((state) => ({
        sync: {
          ...state.sync,
          oldestSyncSettings: {
            global: syncSettings.global_oldest_sync_timestamp || null,
            chats: chats,
            isLoaded: true,
          }
        }
      }));

      return { success: true };
    } catch (error) {
      console.error('加载同步设置失败:', error);
      return { success: false, error: error.message };
    }
  },

  /**
   * 设置全局最旧同步时间戳
   * @param {string|null} timestamp - ISO 8601格式的时间戳，null表示移除设置
   * @returns {Promise} 设置操作的Promise
   */
  setGlobalOldestSyncTimestamp: async (timestamp) => {
    try {
      const response = await setGlobalOldestSyncTimestamp(timestamp);

      if (response.success) {
        // 操作成功后，重新加载最新的同步设置数据
        const { loadSyncSettings } = useSettingsStore.getState();
        await loadSyncSettings(true); // 强制刷新
      }

      return response;
    } catch (error) {
      console.error('设置全局最旧同步时间戳失败:', error);
      return { success: false, error: error.message };
    }
  },

  /**
   * 设置特定聊天的最旧同步时间戳
   * @param {number} chatId - 聊天ID
   * @param {string|null} timestamp - ISO 8601格式的时间戳，null表示移除设置
   * @returns {Promise} 设置操作的Promise
   */
  setChatOldestSyncTimestamp: async (chatId, timestamp) => {
    try {
      const response = await setChatOldestSyncTimestamp(chatId, timestamp);

      if (response.success) {
        // 操作成功后，重新加载最新的同步设置数据
        const { loadSyncSettings } = useSettingsStore.getState();
        await loadSyncSettings(true); // 强制刷新
      }

      return response;
    } catch (error) {
      console.error('设置聊天最旧同步时间戳失败:', error);
      return { success: false, error: error.message };
    }
  },

  /**
   * 获取特定聊天的最旧同步时间戳
   * @param {number} chatId - 聊天ID
   * @returns {Promise} 获取操作的Promise
   */
  getChatOldestSyncTimestamp: async (chatId) => {
    try {
      const response = await getChatOldestSyncTimestamp(chatId);
      return response;
    } catch (error) {
      console.error('获取聊天最旧同步时间戳失败:', error);
      return { success: false, error: error.message };
    }
  },
  
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
   * 从后端API获取白名单数据
   */
  loadWhitelist: async () => {
    try {
      const response = await getWhitelist();
      const items = response.whitelist || [];
      
      set({
        whitelist: {
          items: items,
          isLoaded: true
        }
      });
      
      return items;
    } catch (error) {
      console.error('加载白名单失败:', error);
      throw error;
    }
  },

  /**
   * 添加到白名单
   * @param {number} chatId - 要添加的聊天ID
   */
  addToWhitelistAction: async (chatId) => {
    try {
      const response = await addToWhitelist(chatId);
      
      // 如果添加成功，更新本地状态
      if (response.success) {
        set((state) => ({
          whitelist: {
            ...state.whitelist,
            items: [...state.whitelist.items, chatId]
          }
        }));
      }
      
      return response;
    } catch (error) {
      console.error('添加到白名单失败:', error);
      throw error;
    }
  },

  /**
   * 从白名单移除
   * @param {number} chatId - 要移除的聊天ID
   */
  removeFromWhitelistAction: async (chatId) => {
    try {
      const response = await removeFromWhitelist(chatId);

      // 如果移除成功，更新本地状态
      if (response.success) {
        set((state) => ({
          whitelist: {
            ...state.whitelist,
            items: state.whitelist.items.filter(item => item !== chatId)
          }
        }));
      }

      return response;
    } catch (error) {
      console.error('从白名单移除失败:', error);
      throw error;
    }
  },

  /**
   * 检查特定ID是否在白名单中
   * @param {number} chatId - 要检查的聊天ID
   * @returns {boolean} 是否在白名单中
   */
  isInWhitelist: (chatId) => {
    const state = useSettingsStore.getState();
    return state.whitelist.items.includes(chatId);
  },
}));

export default useSettingsStore;