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
  
  // 获取当前选中的导航项和底部导航栏显示状态
  const { activeNav, isBottomNavVisible } = useNavStore();

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

  return (
    <div className="app-container">
      {/* 主内容区域 */}
      <main className="app-main">
        {/* 用户信息显示区域 - 仅在Telegram环境中显示 */}
        {isAvailable && userInfo && (
          <div className="user-info-banner">
            <span className="user-name">
              欢迎，{getUserDisplayName()}
              {userInfo.username ? ` (@${userInfo.username})` : ''}
            </span>
          </div>
        )}
        
        {renderPage()}
      </main>
      
      {/* 底部导航栏 - 根据状态控制显示/隐藏 */}
      {isBottomNavVisible && <BottomNavBar />}
    </div>
  );
}

export default App;
