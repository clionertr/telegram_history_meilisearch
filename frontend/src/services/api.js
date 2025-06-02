/**
 * API服务 - 封装用于与后端API通信的函数
 */

// API基础URL，可以从环境变量获取
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? 'http://localhost:8000' : '');

/**
 * 搜索API - 调用后端/api/v1/search端点
 * @param {string} query - 搜索关键词
 * @param {Object} filters - 过滤条件 {chat_type, date_from, date_to}
 * @param {number} page - 当前页码，从1开始
 * @param {number} hitsPerPage - 每页结果数量
 * @returns {Promise} - 搜索结果Promise
 */
export const searchMessages = async (query, filters = {}, page = 1, hitsPerPage = 10) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        filters,
        page,
        hits_per_page: hitsPerPage
      }),
    });

    // 如果响应不成功，抛出错误
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `搜索请求失败 (${response.status}: ${response.statusText})`
      );
    }

    // 解析并返回响应数据
    return await response.json();
  } catch (error) {
    console.error('API调用失败:', error);
    throw error; // 重新抛出错误以便调用者可以处理
  }
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
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/dialogs?page=${page}&limit=${limit}&include_avatars=${include_avatars}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `获取会话列表失败 (${response.status}: ${response.statusText})`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('获取会话列表API调用失败:', error);
    throw error;
  }
};

export default {
  searchMessages,
  getWhitelist,
  addToWhitelist,
  removeFromWhitelist,
  getCacheTypes,
  clearCacheTypes,
  clearAllCache,
  getDialogs
};