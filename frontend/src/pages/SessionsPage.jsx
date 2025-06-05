import React, { useEffect, useState } from 'react';
import useTelegramSDK from '../hooks/useTelegramSDK';
import { useSessionsStore } from '../store/sessionsStore.js';
import { addToWhitelist, removeFromWhitelist } from '../services/api';
import useSettingsStore from '../store/settingsStore';
import SessionSearchBar from '../components/SessionSearchBar';

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
    isSearchMode,
    isSearching,
    searchError,
    fetchSessions,
    changePage,
    searchChangePage,
    refreshSessionsCache,
    clearAvatarCache,
    fetchCacheStatus,
    getCacheInfo
  } = useSessionsStore();

  // 使用设置store获取白名单数据
  const {
    whitelist,
    loadWhitelist,
    addToWhitelistAction,
    removeFromWhitelistAction
  } = useSettingsStore();

  // 本地状态管理
  const [processingWhitelist, setProcessingWhitelist] = useState(new Set()); // 正在处理白名单操作的会话ID集合
  const [toastMessage, setToastMessage] = useState(''); // Toast消息
  const [showCacheStats, setShowCacheStats] = useState(false);
  const [cacheInfo, setCacheInfo] = useState({});

  // 初始加载
  useEffect(() => {
    fetchSessions(1);
    fetchCacheStatus();
    // 加载白名单数据
    if (!whitelist.isLoaded) {
      loadWhitelist().catch(error => {
        console.error('加载白名单失败:', error);
      });
    }
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
    
    // 根据当前模式选择不同的分页方法
    if (isSearchMode) {
      await searchChangePage(page);
    } else {
      await changePage(page);
    }
    
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

  // 检查会话是否在白名单中
  const isSessionInWhitelist = (sessionId) => {
    return whitelist.items.includes(sessionId);
  };

  // 切换白名单状态
  const handleToggleWhitelist = async (sessionId, sessionName) => {
    const isInWhitelist = isSessionInWhitelist(sessionId);

    try {
      setProcessingWhitelist(prev => new Set([...prev, sessionId]));

      if (isInWhitelist) {
        // 从白名单移除
        await removeFromWhitelistAction(sessionId);
        setToastMessage(`已将 "${sessionName}" 从白名单移除`);
      } else {
        // 添加到白名单
        await addToWhitelistAction(sessionId);
        setToastMessage(`已将 "${sessionName}" 添加到白名单`);
      }

      // 触发触觉反馈
      try {
        triggerHapticFeedback('success');
      } catch (error) {
        console.warn('触发触觉反馈失败:', error);
      }
    } catch (error) {
      console.error('白名单操作失败:', error);
      const operation = isInWhitelist ? '移除' : '添加';
      setToastMessage(`${operation}失败: ${error.message}`);

      // 触发错误反馈
      try {
        triggerHapticFeedback('error');
      } catch (e) {
        console.warn('触发触觉反馈失败:', e);
      }
    } finally {
      setProcessingWhitelist(prev => {
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
          className={`px-3 py-1 mx-1 rounded transition-theme ${
            i === currentPage
              ? 'bg-accent-primary text-white'
              : 'bg-bg-secondary text-text-primary border border-border-primary hover:bg-bg-tertiary'
          }`}
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
          className="px-3 py-1 rounded bg-bg-secondary text-text-primary border border-border-primary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-theme"
        >
          上一页
        </button>
        
        {pages}
        
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="px-3 py-1 rounded bg-bg-secondary text-text-primary border border-border-primary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-theme"
        >
          下一页
        </button>
      </div>
    );
  };

  return (
    <div className="bg-bg-primary text-text-primary min-h-screen transition-theme">
      <div className="max-w-4xl mx-auto p-6">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 text-text-primary transition-theme">
            会话列表
          </h1>
          
          <div className="flex justify-center items-center space-x-4 mb-4">
            {/* 缓存状态指示器 */}
            <button
              onClick={() => setShowCacheStats(!showCacheStats)}
              className="text-sm text-text-secondary hover:text-text-primary transition-theme"
            >
              {cacheInfo.isCacheInitialized ? (
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-success rounded-full mr-2"></span>
                  缓存已启用
                </span>
              ) : (
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-text-tertiary rounded-full mr-2"></span>
                  未缓存
                </span>
              )}
            </button>

            {/* 操作按钮 */}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="px-4 py-2 bg-accent-primary text-white rounded hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-theme"
            >
              {isLoading ? '刷新中...' : '刷新缓存'}
            </button>
            
            <button
              onClick={handleClearAvatars}
              className="px-4 py-2 bg-warning text-white rounded hover:bg-warning/90 transition-theme"
            >
              清除头像
            </button>
          </div>

          {/* 会话搜索栏 */}
          <SessionSearchBar />

          {/* 缓存统计信息 */}
          {showCacheStats && (
            <div className="mb-6 p-4 bg-bg-secondary border border-border-primary rounded-lg transition-theme">
              <h3 className="text-lg font-semibold mb-2 text-text-primary transition-theme">缓存统计</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-text-secondary transition-theme">缓存状态:</span>
                  <span className="ml-2 font-medium text-text-primary transition-theme">
                    {cacheInfo.isCacheInitialized ? '已启用' : '未启用'}
                  </span>
                </div>
                <div>
                  <span className="text-text-secondary transition-theme">缓存大小:</span>
                  <span className="ml-2 font-medium text-text-primary transition-theme">{cacheInfo.cacheSize || 0} 个会话</span>
                </div>
                <div>
                  <span className="text-text-secondary transition-theme">缓存年龄:</span>
                  <span className="ml-2 font-medium text-text-primary transition-theme">
                    {formatCacheAge(cacheInfo.cacheAge) || '无'}
                  </span>
                </div>
              </div>
            </div>
          )}
          
        </header>

        {(isLoading || isSearching) && (
          <div>
            {/* 分页信息骨架 */}
            <div className="text-center mb-4 animate-pulse">
              <div className="h-4 bg-bg-tertiary rounded w-48 mx-auto transition-theme"></div>
            </div>
            
            {/* 会话列表骨架 */}
            <div className="space-y-4">
              {Array.from({ length: Math.min(pageSize, 5) }).map((_, index) => (
                <div key={`skeleton-${index}`} className="animate-pulse flex items-center space-x-4 p-4 border-b border-border-primary">
                  <div className="rounded-full bg-bg-tertiary h-12 w-12 transition-theme"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-bg-tertiary rounded w-3/4 transition-theme"></div>
                    <div className="h-3 bg-bg-tertiary rounded w-1/2 transition-theme"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* 显示错误信息 */}
        {(error || searchError) && !isLoading && !isSearching && (
          <div className="text-center py-10 text-error transition-theme">
            <div className="text-4xl mb-3">⚠️</div>
            {isSearchMode ? `搜索失败: ${searchError}` : `加载失败: ${error}`}
          </div>
        )}
        
        {!isLoading && !isSearching && !error && !searchError && sessions.length === 0 && (
          <div className="text-center py-10 text-text-secondary transition-theme">
            <div className="text-4xl mb-3">🤷</div>
            <p>{isSearchMode ? '没有找到匹配的会话' : '没有找到会话'}</p>
          </div>
        )}

        {!isLoading && !isSearching && !error && !searchError && sessions.length > 0 && (
          <>
            {/* 分页信息 */}
            {totalSessions > 0 && (
              <div className="text-center mb-4 text-text-secondary transition-theme">
                <p className="text-sm">
                  {isSearchMode ? (
                    <>搜索到 {totalSessions} 个会话，当前显示第 {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalSessions)} 个</>
                  ) : (
                    <>共 {totalSessions} 个会话，当前显示第 {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalSessions)} 个</>
                  )}
                </p>
              </div>
            )}

            <div className="space-y-4">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="bg-bg-secondary rounded-lg p-4 border border-border-primary shadow-theme-sm hover:shadow-theme-md transition-theme"
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
                          className="w-12 h-12 rounded-full bg-bg-tertiary flex items-center justify-center text-text-secondary text-lg font-medium transition-theme"
                          style={{
                            display: session.avatar_base64 && session.avatar_base64 !== null ? 'none' : 'flex'
                          }}
                        >
                          {session.name ? session.name.charAt(0).toUpperCase() : '?'}
                        </div>
                      </div>
                      
                      {/* 会话信息 */}
                      <div className="flex-1 min-w-0">
                        <h4 className="text-lg font-medium mb-1 truncate text-text-primary transition-theme">
                          {session.name}
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-text-secondary transition-theme">
                              类型: {session.type}
                            </span>
                            <span className="text-text-secondary transition-theme">
                              ID: {session.id}
                            </span>
                          </div>
                          {session.unread_count > 0 && (
                            <div className="flex items-center">
                              <span className="text-xs bg-error/10 text-error px-2 py-1 rounded transition-theme">
                                {session.unread_count} 条未读消息
                              </span>
                            </div>
                          )}
                          {session.date && (
                            <p className="text-xs text-text-tertiary transition-theme">
                              最后活动: {formatTime(session.date)}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* 右侧：操作按钮 */}
                    <div className="flex-shrink-0 ml-4">
                      {(() => {
                        const isInWhitelist = isSessionInWhitelist(session.id);
                        const isProcessing = processingWhitelist.has(session.id);

                        return (
                          <button
                            onClick={() => handleToggleWhitelist(session.id, session.name)}
                            disabled={isProcessing}
                            className={`px-4 py-2 text-sm font-medium rounded transition-theme ${
                              isProcessing
                                ? 'bg-bg-tertiary text-text-tertiary cursor-not-allowed'
                                : isInWhitelist
                                ? 'bg-error text-white hover:bg-error/80'
                                : 'bg-accent-primary text-white hover:bg-accent-hover'
                            }`}
                          >
                            <span className="flex items-center">
                              {isProcessing ? (
                                <>
                                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  {isInWhitelist ? '移除中...' : '添加中...'}
                                </>
                              ) : isInWhitelist ? (
                                <>
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                  取消白名单
                                </>
                              ) : (
                                <>
                                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                  </svg>
                                  加入白名单
                                </>
                              )}
                            </span>
                          </button>
                        );
                      })()}
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
          <div className="mt-6 p-3 bg-success/10 border border-success text-success rounded text-sm transition-theme">
            ⚡ 缓存已启用：页面切换瞬时完成，头像已在启动时预下载
          </div>
        )}

        {/* Toast 消息 */}
        {toastMessage && (
          <div className="fixed bottom-4 right-4 bg-bg-primary text-text-primary border border-border-primary px-4 py-2 rounded shadow-theme-lg z-50 transition-theme">
            {toastMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionsPage;