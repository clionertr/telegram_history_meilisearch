import { useEffect } from 'react';
import SearchPage from './pages/SearchPage';
import SessionsPage from './pages/SessionsPage';
import SettingsPage from './pages/SettingsPage';
import BottomNavBar from './components/navigation/BottomNavBar';
import ThemeToggle from './components/common/ThemeToggle';
import useTelegramSDK from './hooks/useTelegramSDK';
import useTheme from './hooks/useTheme';
import useNavStore from './store/navStore';
import './App.css';

/**
 * 应用主组件 - 阶段3重构版本 + 主题系统
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
  
  // 使用主题系统
  const { isInitializing: isThemeInitializing } = useTheme();
  
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
      case 'sessions':
        return <SessionsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <SearchPage />;
    }
  };

  // 主题系统初始化时显示加载状态
  if (isThemeInitializing) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-text-secondary">正在初始化主题系统...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container bg-bg-primary text-text-primary transition-theme">
      {/* 顶部工具栏 */}
      <header className="sticky top-0 z-40 bg-bg-primary/95 backdrop-blur-sm border-b border-border-primary">
        <div className="flex items-center justify-between px-4 py-2">
          {/* 用户信息显示区域 - 仅在Telegram环境中显示 */}
          <div className="flex-1">
            {isAvailable && userInfo && (
              <div className="user-info-banner">
                <span className="user-name text-text-primary">
                  欢迎，{getUserDisplayName()}
                  {userInfo.username ? ` (@${userInfo.username})` : ''}
                </span>
              </div>
            )}
          </div>
          
          {/* 主题切换按钮 */}
          <div className="flex items-center space-x-2">
            <ThemeToggle mode="simple" size="medium" />
          </div>
        </div>
      </header>
      
      {/* 主内容区域 */}
      <main className="app-main flex-1 bg-bg-primary">
        {renderPage()}
      </main>
      
      {/* 底部导航栏 - 根据状态控制显示/隐藏 */}
      {isBottomNavVisible && <BottomNavBar />}
    </div>
  );
}

export default App;
