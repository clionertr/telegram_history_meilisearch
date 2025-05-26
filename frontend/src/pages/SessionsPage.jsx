import { useEffect } from 'react';
import useTelegramSDK from '../hooks/useTelegramSDK';
import useSessionsStore from '../store/sessionsStore';
import SettingsCard from '../components/settings/SettingsCard'; // 复用卡片样式

/**
 * 会话页面组件
 * 用于展示用户会话列表
 */
function SessionsPage() {
  const { isAvailable, themeParams } = useTelegramSDK();
  const {
    sessions,
    isLoading,
    error,
    fetchSessions,
    currentPage,
    // totalPages, // 暂时未使用，因为后端未提供总数
    // setCurrentPage, // 分页功能后续添加
  } = useSessionsStore();

  useEffect(() => {
    fetchSessions(currentPage); // 初始加载第一页
  }, [fetchSessions, currentPage]);

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

  return (
    <div
      className="w-full max-w-4xl mx-auto px-4 pt-6 pb-20" // 调整padding，特别是pb以避免被导航栏遮挡
      style={pageStyle}
    >
      <header className="text-center mb-6">
        <h1 className="text-3xl font-semibold" style={textStyle}>
          会话列表
        </h1>
      </header>

      {isLoading && (
        <div className="text-center py-10" style={hintStyle}>
          <div className="text-4xl mb-3">⏳</div>
          正在加载会话...
        </div>
      )}
      {error && (
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
        <div className="space-y-4">
          {sessions.map((session) => (
            <SettingsCard key={session.id} title={session.name || '未知会话'}>
              <div className="p-4">
                <p className="text-sm" style={hintStyle}>
                  ID: {session.id}
                </p>
                <p className="text-sm font-medium" style={textStyle}>
                  类型: {getSessionTypeDisplay(session.type)}
                </p>
                {/* 后续添加头像和白名单按钮 */}
              </div>
            </SettingsCard>
          ))}
        </div>
      )}
      
      {/* 分页控件后续添加 */}
    </div>
  );
}

export default SessionsPage;