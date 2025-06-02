import React, { useEffect, useState } from 'react';
import useTelegramSDK from '../hooks/useTelegramSDK';
import { useSessionsStore } from '../store/sessionsStore.js';
import { addToWhitelist } from '../services/api';

/**
 * 会话页面组件
 * 用于展示用户会话列表
 */
const SessionsPage = () => {
  const { isAvailable, themeParams, triggerHapticFeedback } = useTelegramSDK();
  
  // 使用会话store
  const {
    sessions,
    currentPage,
    totalPages,
    totalSessions,
    pageSize,
    isLoading,
    isLoadingAvatars,
    error,
    cacheStatus,
    fetchSessions,
    changePage,
    refreshSessionsCache,
    clearAvatarCache,
    fetchCacheStatus,
    getCacheInfo
  } = useSessionsStore();

  // 本地状态管理
  const [addingToWhitelist, setAddingToWhitelist] = useState(new Set()); // 正在添加到白名单的会话ID集合
  const [toastMessage, setToastMessage] = useState(''); // Toast消息
  const [showCacheStats, setShowCacheStats] = useState(false);
  const [cacheInfo, setCacheInfo] = useState({});

  // 初始加载
  useEffect(() => {
    fetchSessions(1);
    fetchCacheStatus();
  }, []);

  // 更新缓存信息
  const updateCacheInfo = () => {
    const info = getCacheInfo();
    setCacheInfo(info);
  };

  // 定期更新缓存信息
  useEffect(() => {
    updateCacheInfo();
    const interval = setInterval(updateCacheInfo, 5000);
    return () => clearInterval(interval);
  }, []);

  // 页面切换处理
  const handlePageChange = async (page) => {
    if (page < 1 || page > totalPages) return;
    await changePage(page);
    
    // 触发触觉反馈
    try {
      triggerHapticFeedback('selection');
    } catch (error) {
      console.warn('触发触觉反馈失败:', error);
    }
    
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 手动刷新
  const handleRefresh = async () => {
    await refreshSessionsCache();
    await fetchCacheStatus();
    updateCacheInfo();
  };

  // 清除头像缓存
  const handleClearAvatars = async () => {
    await clearAvatarCache();
    await fetchCacheStatus();
    updateCacheInfo();
  };

  // Toast消息自动消失
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(''), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // 添加到白名单
  const handleAddToWhitelist = async (sessionId, sessionName) => {
    try {
      setAddingToWhitelist(prev => new Set([...prev, sessionId]));
      
      await addToWhitelist(sessionId);
      
      setToastMessage(`已将 "${sessionName}" 添加到白名单`);
      
      // 触发触觉反馈
      try {
        triggerHapticFeedback('success');
      } catch (error) {
        console.warn('触发触觉反馈失败:', error);
      }
    } catch (error) {
      console.error('添加到白名单失败:', error);
      setToastMessage(`添加失败: ${error.message}`);
      
      // 触发错误反馈
      try {
        triggerHapticFeedback('error');
      } catch (e) {
        console.warn('触发触觉反馈失败:', e);
      }
    } finally {
      setAddingToWhitelist(prev => {
        const newSet = new Set(prev);
        newSet.delete(sessionId);
        return newSet;
      });
    }
  };

  // 格式化时间
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-CN');
  };

  // 格式化缓存年龄
  const formatCacheAge = (ageMs) => {
    if (!ageMs) return '';
    const seconds = Math.floor(ageMs / 1000);
    if (seconds < 60) return `${seconds}秒前`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    const hours = Math.floor(minutes / 60);
    return `${hours}小时前`;
  };

  // 页面样式
  const pageStyle = {
    backgroundColor: themeParams?.bg_color || '#ffffff',
    color: themeParams?.text_color || '#000000',
    minHeight: '100vh',
  };

  const textStyle = {
    color: themeParams?.text_color || '#000000',
  };

  const hintStyle = {
    color: themeParams?.hint_color || '#999999',
  };

  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pages = [];
    const maxVisiblePages = 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`px-3 py-1 mx-1 rounded ${
            i === currentPage
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
          }`}
          style={i === currentPage ? { backgroundColor: themeParams?.button_color || '#3b82f6' } : {}}
        >
          {i}
        </button>
      );
    }

    return (
      <div className="flex justify-center items-center mt-6 space-x-2">
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          上一页
        </button>
        
        {pages}
        
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一页
        </button>
      </div>
    );
  };

  return (
    <div style={pageStyle}>
      <div className="max-w-4xl mx-auto p-6">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2" style={textStyle}>
            会话列表
          </h1>
          
          <div className="flex justify-center items-center space-x-4 mb-4">
            {/* 缓存状态指示器 */}
            <button
              onClick={() => setShowCacheStats(!showCacheStats)}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              {cacheInfo.isCacheInitialized ? (
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  缓存已启用
                </span>
              ) : (
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                  未缓存
                </span>
              )}
            </button>

            {/* 操作按钮 */}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: themeParams?.button_color || '#3b82f6' }}
            >
              {isLoading ? '刷新中...' : '刷新缓存'}
            </button>
            
            <button
              onClick={handleClearAvatars}
              className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
            >
              清除头像
            </button>
          </div>

          {/* 缓存统计信息 */}
          {showCacheStats && (
            <div className="mb-6 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">缓存统计</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">缓存状态:</span>
                  <span className="ml-2 font-medium">
                    {cacheInfo.isCacheInitialized ? '已启用' : '未启用'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">缓存大小:</span>
                  <span className="ml-2 font-medium">{cacheInfo.cacheSize || 0} 个会话</span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">缓存年龄:</span>
                  <span className="ml-2 font-medium">
                    {formatCacheAge(cacheInfo.cacheAge) || '无'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">头像加载:</span>
                  <span className="ml-2 font-medium">
                    {isLoadingAvatars ? '加载中...' : '完成'}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          {isLoadingAvatars && !isLoading && (
            <div className="text-sm mt-2" style={hintStyle}>
              <span className="inline-flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                正在加载头像...
              </span>
            </div>
          )}
        </header>

        {isLoading && (
          <div>
            {/* 分页信息骨架 */}
            <div className="text-center mb-4 animate-pulse">
              <div className="h-4 bg-gray-300 rounded w-48 mx-auto"></div>
            </div>
            
            {/* 会话列表骨架 */}
            <div className="space-y-4">
              {Array.from({ length: Math.min(pageSize, 5) }).map((_, index) => (
                <div key={`skeleton-${index}`} className="animate-pulse flex items-center space-x-4 p-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="rounded-full bg-gray-300 dark:bg-gray-600 h-12 w-12"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {error && !isLoading && (
          <div className="text-center py-10 text-red-500" style={hintStyle}>
            <div className="text-4xl mb-3">⚠️</div>
            加载失败: {error}
          </div>
        )}
        
        {!isLoading && !error && sessions.length === 0 && (
          <div className="text-center py-10" style={hintStyle}>
            <div className="text-4xl mb-3">🤷</div>
            <p>没有找到会话</p>
          </div>
        )}

        {!isLoading && !error && sessions.length > 0 && (
          <>
            {/* 分页信息 */}
            {totalSessions > 0 && (
              <div className="text-center mb-4" style={hintStyle}>
                <p className="text-sm">
                  共 {totalSessions} 个会话，当前显示第 {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalSessions)} 个
                </p>
              </div>
            )}

            <div className="space-y-4">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow"
                  style={{
                    backgroundColor: themeParams?.secondary_bg_color || '#ffffff'
                  }}
                >
                  <div className="flex items-center justify-between">
                    {/* 左侧：头像和信息 */}
                    <div className="flex items-center flex-1">
                      {/* 头像 */}
                      <div className="flex-shrink-0 mr-4">
                        {session.avatar_base64 && session.avatar_base64 !== null ? (
                          <img
                            src={session.avatar_base64}
                            alt={session.name}
                            className="w-12 h-12 rounded-full object-cover"
                            onError={(e) => {
                              console.warn(`头像加载失败: ${session.name}`, e);
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'flex';
                            }}
                          />
                        ) : null}
                        <div 
                          className="w-12 h-12 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-300 text-lg font-medium"
                          style={{
                            display: session.avatar_base64 && session.avatar_base64 !== null ? 'none' : 'flex'
                          }}
                        >
                          {isLoadingAvatars ? (
                            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            session.name ? session.name.charAt(0).toUpperCase() : '?'
                          )}
                        </div>
                      </div>
                      
                      {/* 会话信息 */}
                      <div className="flex-1 min-w-0">
                        <h4 
                          className="text-lg font-medium mb-1 truncate" 
                          style={{ color: themeParams?.text_color || '#000000' }}
                        >
                          {session.name}
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span style={{ color: themeParams?.hint_color || '#666666' }}>
                              类型: {session.type}
                            </span>
                            <span style={{ color: themeParams?.hint_color || '#666666' }}>
                              ID: {session.id}
                            </span>
                          </div>
                          {session.unread_count > 0 && (
                            <div className="flex items-center">
                              <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                                {session.unread_count} 条未读消息
                              </span>
                            </div>
                          )}
                          {session.date && (
                            <p className="text-xs" style={{ color: themeParams?.hint_color || '#999999' }}>
                              最后活动: {formatTime(session.date)}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* 右侧：操作按钮 */}
                    <div className="flex-shrink-0 ml-4">
                      <button
                        onClick={() => handleAddToWhitelist(session.id, session.name)}
                        disabled={addingToWhitelist.has(session.id)}
                        className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
                          addingToWhitelist.has(session.id)
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-green-500 text-white hover:bg-green-600'
                        }`}
                        style={addingToWhitelist.has(session.id) ? {} : { backgroundColor: themeParams?.button_color || '#10B981' }}
                      >
                        {addingToWhitelist.has(session.id) ? '添加中...' : '加入白名单'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
        
        {/* 分页控件 */}
        {!isLoading && !error && totalPages > 1 && (
          <div className="mt-8 flex justify-center items-center space-x-4">
            {renderPagination()}
          </div>
        )}

        {/* 性能提示 */}
        {cacheInfo.isCacheInitialized && !isLoading && (
          <div className="mt-6 p-3 bg-green-100 dark:bg-green-900/30 border border-green-400 text-green-700 dark:text-green-300 rounded text-sm">
            ⚡ 缓存已启用：页面切换瞬时完成，头像按需加载
          </div>
        )}

        {/* Toast 消息 */}
        {toastMessage && (
          <div className="fixed bottom-4 right-4 bg-black text-white px-4 py-2 rounded shadow-lg z-50">
            {toastMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionsPage;