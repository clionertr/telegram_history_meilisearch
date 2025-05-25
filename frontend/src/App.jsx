import { useEffect } from 'react';
import SearchPage from './pages/SearchPage';
import GroupsPage from './pages/GroupsPage';
import SettingsPage from './pages/SettingsPage';
import BottomNavBar from './components/navigation/BottomNavBar';
import useTelegramSDK from './hooks/useTelegramSDK';
import useNavStore from './store/navStore';
import './App.css';

/**
 * 应用主组件 - 阶段3重构版本
 */
function App() {
  // 使用自定义TMA SDK钩子
  const {
    isInitialized,
    isAvailable,
    userInfo,
    themeParams,
    getThemeCssVars
  } = useTelegramSDK();
  
  // 获取当前选中的导航项
  const { activeNav } = useNavStore();

  // 将Telegram主题应用到整个应用
  useEffect(() => {
    if (isInitialized && themeParams) {
      try {
        // 获取CSS变量对象
        const cssVars = getThemeCssVars();
        
        // 将CSS变量应用到根元素，但保持我们的设计系统优先
        const root = document.documentElement;
        Object.entries(cssVars).forEach(([key, value]) => {
          // 只应用特定的Telegram主题变量，避免覆盖我们的设计系统
          if (key.includes('--tg-theme')) {
            root.style.setProperty(key, value);
          }
        });
      } catch (error) {
        console.error('应用主题到根元素失败:', error);
      }
    }
  }, [isInitialized, themeParams, getThemeCssVars]);

  // 处理用户显示名称
  const getUserDisplayName = () => {
    if (!userInfo) return '';
    
    let displayName = userInfo.firstName || '';
    if (userInfo.lastName) {
      displayName += ` ${userInfo.lastName}`;
    }
    return displayName.trim() || '用户';
  };
  
  // 根据当前选中的导航项渲染对应页面
  const renderPage = () => {
    switch (activeNav) {
      case 'search':
        return <SearchPage />;
      case 'groups':
        return <GroupsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <SearchPage />;
    }
  };

  // 获取页面标题
  const getPageTitle = () => {
    switch (activeNav) {
      case 'search':
        return 'Telegram 中文历史消息搜索';
      case 'groups':
        return '群组';
      case 'settings':
        return '设置';
      default:
        return 'Telegram 中文历史消息搜索';
    }
  };

  return (
    <div className="app-container">
      {/* 头部导航栏 */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="page-title">{getPageTitle()}</h1>
          {/* 用户信息显示区域 - 仅在Telegram环境中显示 */}
          {isAvailable && userInfo && (
            <div className="user-info">
              <span className="user-name">
                {getUserDisplayName()}
                {userInfo.username ? ` (@${userInfo.username})` : ''}
              </span>
            </div>
          )}
        </div>
      </header>
      
      {/* 主内容区域 */}
      <main className="app-main">
        {renderPage()}
      </main>
      
      {/* 底部导航栏 */}
      <BottomNavBar />
    </div>
  );
}

export default App;
