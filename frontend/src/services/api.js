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

export default {
  searchMessages,
  getWhitelist,
  addToWhitelist,
  removeFromWhitelist
};