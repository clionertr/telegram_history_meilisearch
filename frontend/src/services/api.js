/**
 * API服务 - 封装用于与后端API通信的函数
 */

// API基础URL，可以从环境变量获取
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

export default {
  searchMessages
};