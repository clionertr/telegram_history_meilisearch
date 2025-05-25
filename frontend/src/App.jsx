import { useEffect } from 'react';
import SearchPage from './pages/SearchPage';
import GroupsPage from './pages/GroupsPage';
import SettingsPage from './pages/SettingsPage';
import BottomNavBar from './components/navigation/BottomNavBar';
import useTelegramSDK from './hooks/useTelegramSDK';
import useNavStore from './store/navStore';
import './App.css';

/**
 * 应用主组件
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
        
        // 将CSS变量应用到根元素
        const root = document.documentElement;
        Object.entries(cssVars).forEach(([key, value]) => {
          root.style.setProperty(key, value);
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
    <div
      className="min-h-screen text-gray-900 dark:text-gray-100 pb-16" // 添加底部内边距，为导航栏留出空间
      style={isAvailable ? {
        backgroundColor: 'var(--tg-theme-bg-color, rgb(243 244 246))',
        color: 'var(--tg-theme-text-color, rgb(17 24 39))'
      } : {
        backgroundColor: 'rgb(243 244 246)',
        color: 'rgb(17 24 39)'
      }}
    >
      {/* 用户信息显示区域 */}
      {isAvailable && userInfo && (
        <div
          className="p-2 text-center"
          style={{
            backgroundColor: 'var(--tg-theme-secondary-bg-color, rgb(219 234 254))',
            color: 'var(--tg-theme-text-color, rgb(17 24 39))',
          }}
        >
          <p className="text-sm">
            欢迎，{getUserDisplayName()}
            {userInfo.username ? ` (@${userInfo.username})` : ''}
          </p>
        </div>
      )}
      
      {/* 主内容区域 - 根据导航切换 */}
      {renderPage()}
      
      {/* 底部导航栏 */}
      <BottomNavBar />
    </div>
  );
}

export default App;
