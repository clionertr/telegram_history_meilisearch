import { useEffect, useState } from 'react';
import useTelegramSDK from '../hooks/useTelegramSDK';
import useSessionsStore from '../store/sessionsStore';
import SettingsCard from '../components/settings/SettingsCard'; // 复用卡片样式
import { addToWhitelist } from '../services/api';

/**
 * 会话页面组件
 * 用于展示用户会话列表
 */
function SessionsPage() {
  const { isAvailable, themeParams, triggerHapticFeedback } = useTelegramSDK();
  const {
    sessions,
    isLoading,
    isLoadingAvatars,
    error,
    fetchSessionsFast, // 使用快速加载
    currentPage,
    totalPages,
    totalSessions,
    itemsPerPage,
    setCurrentPage,
  } = useSessionsStore();

  // 本地状态管理
  const [addingToWhitelist, setAddingToWhitelist] = useState(new Set()); // 正在添加到白名单的会话ID集合
  const [toastMessage, setToastMessage] = useState(''); // Toast消息

  useEffect(() => {
    fetchSessionsFast(currentPage); // 初始加载第一页（快速模式）
  }, [fetchSessionsFast, currentPage]);

  // Toast消息自动消失
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => {
        setToastMessage('');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // 处理添加到白名单
  const handleAddToWhitelist = async (sessionId, sessionName) => {
    if (addingToWhitelist.has(sessionId)) return; // 防止重复点击

    setAddingToWhitelist(prev => new Set(prev).add(sessionId));
    
    try {
      await addToWhitelist(sessionId);
      setToastMessage(`已成功将 "${sessionName}" 添加到白名单`);
      
      // 触发触觉反馈
      try {
        triggerHapticFeedback('success');
      } catch (error) {
        console.warn('触发触觉反馈失败:', error);
      }
    } catch (error) {
      console.error('添加到白名单失败:', error);
      setToastMessage(`添加 "${sessionName}" 到白名单失败: ${error.message}`);
      
      // 触发错误触觉反馈
      try {
        triggerHapticFeedback('error');
      } catch (hapticError) {
        console.warn('触发触觉反馈失败:', hapticError);
      }
    } finally {
      setAddingToWhitelist(prev => {
        const newSet = new Set(prev);
        newSet.delete(sessionId);
        return newSet;
      });
    }
  };

  // 处理页码变更
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages && newPage !== currentPage) {
      setCurrentPage(newPage);
      
      // 触发触觉反馈
      try {
        triggerHapticFeedback('selection');
      } catch (error) {
        console.warn('触发触觉反馈失败:', error);
      }
      
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // 页面样式
  const pageStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.bg_color,
    minHeight: 'calc(100vh - 60px)', // 减去底部导航栏的高度
  } : {
    backgroundColor: '#f9fafb', // fallback light gray
    minHeight: 'calc(100vh - 60px)',
  };

  // 文本样式
  const textStyle = isAvailable && themeParams ? {
    color: themeParams.text_color,
  } : {};
  
  // 提示文本样式 (用于加载、错误等)
  const hintStyle = isAvailable && themeParams ? {
    color: themeParams.hint_color,
  } : {
    color: 'rgb(107 114 128)', // fallback gray-500
  };

  const getSessionTypeDisplay = (type) => {
    switch (type) {
      case 'user':
        return '用户';
      case 'group':
        return '群组';
      case 'channel':
        return '频道';
      default:
        return '未知';
    }
  };

  // 骨架屏组件
  const SkeletonItem = () => (
    <SettingsCard title="">
      <div className="p-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-full bg-gray-300 mr-3"></div>
            <div>
              <div className="h-4 bg-gray-300 rounded w-24 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-16"></div>
            </div>
          </div>
          <div className="h-6 bg-gray-300 rounded w-16"></div>
        </div>
        <div className="mt-3">
          <div className="h-3 bg-gray-200 rounded w-20 mb-1"></div>
          <div className="h-3 bg-gray-200 rounded w-16"></div>
        </div>
      </div>
    </SettingsCard>
  );

  return (
    <div
      className="w-full max-w-4xl mx-auto px-4 pt-6 pb-20" // 调整padding，特别是pb以避免被导航栏遮挡
      style={pageStyle}
    >
      <header className="text-center mb-6">
        <h1 className="text-3xl font-semibold" style={textStyle}>
          会话列表
        </h1>
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
          <div className="text-center mb-4">
            <div className="h-4 bg-gray-300 rounded w-48 mx-auto animate-pulse"></div>
          </div>
          
          {/* 会话列表骨架 */}
          <div className="space-y-4">
            {Array.from({ length: Math.min(itemsPerPage, 5) }).map((_, index) => (
              <SkeletonItem key={index} />
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
          没有找到会话，或者您还没有任何会话。
        </div>
      )}

      {!isLoading && !error && sessions.length > 0 && (
        <>
          {/* 分页信息 */}
          {totalSessions > 0 && (
            <div className="text-center mb-4" style={hintStyle}>
              <p className="text-sm">
                共 {totalSessions} 个会话，当前显示第 {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, totalSessions)} 个
              </p>
            </div>
          )}

          <div className="space-y-4">
            {sessions.map((session) => (
              <SettingsCard
                key={session.id}
                title={
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center">
                      {session.avatar_base64 ? (
                        <img
                          src={session.avatar_base64}
                          alt={`${session.name || '会话'}头像`}
                          className="w-10 h-10 rounded-full mr-3 object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-xl font-medium mr-3 relative">
                          {isLoadingAvatars ? (
                            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                          ) : (
                            session.name ? session.name.charAt(0).toUpperCase() : 'S'
                          )}
                        </div>
                      )}
                      <span style={textStyle}>{session.name || '未知会话'}</span>
                    </div>
                    
                    {/* 添加到白名单按钮 */}
                    <button
                      onClick={() => handleAddToWhitelist(session.id, session.name)}
                      disabled={addingToWhitelist.has(session.id)}
                      className={`px-3 py-1 text-xs rounded-full transition-colors ${
                        addingToWhitelist.has(session.id)
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-blue-500 text-white hover:bg-blue-600'
                      }`}
                      style={addingToWhitelist.has(session.id) ? {} : { backgroundColor: themeParams?.button_color || '#3b82f6' }}
                    >
                      {addingToWhitelist.has(session.id) ? '添加中...' : '加入白名单'}
                    </button>
                  </div>
                }
              >
                <div className="p-4">
                  <p className="text-sm mb-1" style={hintStyle}>
                    ID: {session.id}
                  </p>
                  <p className="text-sm font-medium" style={textStyle}>
                    类型: {getSessionTypeDisplay(session.type)}
                  </p>
                  <p className="text-xs mt-1" style={hintStyle}>
                    未读: {session.unread_count || 0}
                  </p>
                  {session.date && (
                    <p className="text-xs mt-1" style={hintStyle}>
                      最后活动: {new Date(session.date * 1000).toLocaleString()}
                    </p>
                  )}
                </div>
              </SettingsCard>
            ))}
          </div>
        </>
      )}
      
      {/* 分页控件 */}
      {!isLoading && !error && totalPages > 1 && (
        <div className="mt-8 flex justify-center items-center space-x-4">
          {/* 上一页按钮 */}
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
              currentPage === 1
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
            style={currentPage === 1 ? {} : { backgroundColor: themeParams?.button_color || '#3b82f6' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="mr-2">
              <path
                d="M15 18L9 12L15 6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            上一页
          </button>

          {/* 页码指示器 */}
          <div className="flex items-center space-x-2" style={textStyle}>
            <span className="text-lg font-medium">{currentPage}</span>
            <span>/</span>
            <span className="text-lg">{totalPages}</span>
          </div>

          {/* 下一页按钮 */}
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
              currentPage === totalPages
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
            style={currentPage === totalPages ? {} : { backgroundColor: themeParams?.button_color || '#3b82f6' }}
          >
            下一页
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="ml-2">
              <path
                d="M9 18L15 12L9 6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      )}

      {/* Toast通知 */}
      {toastMessage && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
          <div className="bg-black bg-opacity-80 text-white px-4 py-2 rounded-lg shadow-lg max-w-sm text-center">
            {toastMessage}
          </div>
        </div>
      )}
    </div>
  );
}

export default SessionsPage;