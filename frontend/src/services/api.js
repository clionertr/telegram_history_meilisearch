/**
 * API服务 - 封装用于与后端API通信的函数
 */

// API基础URL，可以从环境变量获取
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? 'http://localhost:8000' : '');

/**
 * 处理API响应
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      }
    } catch (jsonError) {
      // 如果响应不是JSON，使用默认错误消息
      console.warn('无法解析错误响应为JSON:', jsonError);
    }
    
    throw new Error(errorMessage);
  }
  return response.json();
};

/**
 * 通用的API请求方法
 */
const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  return handleResponse(response);
};

/**
 * 搜索API - 调用后端/api/v1/search端点
 * @param {string} query - 搜索关键词
 * @param {Object} filters - 过滤条件 {chat_type, date_from, date_to}
 * @param {number} page - 当前页码，从1开始
 * @param {number} hitsPerPage - 每页结果数量
 * @returns {Promise} - 搜索结果Promise
 */
export const searchMessages = async (query, filters = {}, page = 1, hitsPerPage = 10) => {
  // 构建请求体，符合后端SearchRequest模型
  const requestBody = {
    query,
    page,
    hits_per_page: hitsPerPage,
    filters: {
      chat_type: filters.chat_type || null,
      date_from: filters.date_from || null,
      date_to: filters.date_to || null
    }
  };
  
  return apiRequest('/api/v1/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  });
};

/**
 * 白名单API - 获取白名单列表
 * @returns {Promise} - 白名单数据Promise
 */
export const getWhitelist = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/whitelist`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `获取白名单失败 (${response.status}: ${response.statusText})`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('获取白名单API调用失败:', error);
    throw error;
  }
};

/**
 * 白名单API - 添加到白名单
 * @param {number} chatId - 要添加的聊天ID
 * @returns {Promise} - 操作结果Promise
 */
export const addToWhitelist = async (chatId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/whitelist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chat_id: chatId
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `添加到白名单失败 (${response.status}: ${response.statusText})`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('添加到白名单API调用失败:', error);
    throw error;
  }
};

/**
 * 白名单API - 从白名单移除
 * @param {number} chatId - 要移除的聊天ID
 * @returns {Promise} - 操作结果Promise
 */
export const removeFromWhitelist = async (chatId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/whitelist/${chatId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `从白名单移除失败 (${response.status}: ${response.statusText})`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('从白名单移除API调用失败:', error);
    throw error;
  }
};

/**
 * 缓存API - 获取可清除的缓存类型
 * @returns {Promise} - 缓存类型数据Promise
 */
export const getCacheTypes = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/cache/types`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `获取缓存类型失败 (${response.status}: ${response.statusText})`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('获取缓存类型API调用失败:', error);
    throw error;
  }
};

/**
 * 缓存API - 清除指定类型的缓存
 * @param {Array} cacheTypes - 要清除的缓存类型数组
 * @returns {Promise} - 操作结果Promise
 */
export const clearCacheTypes = async (cacheTypes) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/cache/clear`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        cache_types: cacheTypes
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `清除缓存失败 (${response.status}: ${response.statusText})`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('清除缓存API调用失败:', error);
    throw error;
  }
};

/**
 * 缓存API - 清除所有缓存
 * @returns {Promise} - 操作结果Promise
 */
export const clearAllCache = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/cache/clear/all`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `清除所有缓存失败 (${response.status}: ${response.statusText})`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('清除所有缓存API调用失败:', error);
    throw error;
  }
};

/**
 * Dialogs API - 获取用户会话列表
 * @param {number} page - 当前页码，从1开始
 * @param {number} limit - 每页结果数量
 * @param {boolean} include_avatars - 是否包含头像，默认true。设置为false可大幅提升加载速度
 * @returns {Promise} - 会话列表Promise
 */
export const getDialogs = async (page = 1, limit = 20, include_avatars = true) => {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    include_avatars: include_avatars.toString(),
  });
  
  return apiRequest(`/api/v1/dialogs?${params}`);
};

// 缓存管理API
export const getCacheStatus = async () => {
  return apiRequest('/api/v1/dialogs/cache/status');
};

export const refreshCache = async () => {
  return apiRequest('/api/v1/dialogs/cache/refresh', {
    method: 'POST',
  });
};

export const clearAvatarsCache = async () => {
  return apiRequest('/api/v1/dialogs/cache/avatars', {
    method: 'DELETE',
  });
};

// 同步设置API
export const getSyncSettings = async () => {
  return apiRequest('/api/v1/admin/whitelist/sync_settings');
};

export const setGlobalOldestSyncTimestamp = async (timestamp) => {
  return apiRequest('/api/v1/admin/whitelist/sync_settings/global', {
    method: 'PUT',
    body: JSON.stringify({ timestamp })
  });
};

export const setChatOldestSyncTimestamp = async (chatId, timestamp) => {
  return apiRequest(`/api/v1/admin/whitelist/sync_settings/chat/${chatId}`, {
    method: 'PUT',
    body: JSON.stringify({ timestamp })
  });
};

export const getChatOldestSyncTimestamp = async (chatId) => {
  return apiRequest(`/api/v1/admin/whitelist/sync_settings/chat/${chatId}`);
};

export default {
  searchMessages,
  getWhitelist,
  addToWhitelist,
  removeFromWhitelist,
  getCacheTypes,
  clearCacheTypes,
  clearAllCache,
  getDialogs,
  getCacheStatus,
  refreshCache,
  clearAvatarsCache,
  getSyncSettings,
  setGlobalOldestSyncTimestamp,
  setChatOldestSyncTimestamp,
  getChatOldestSyncTimestamp
};