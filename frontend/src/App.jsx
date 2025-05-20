import { useEffect } from 'react';
import SearchPage from './pages/SearchPage';
import useTelegramSDK from './hooks/useTelegramSDK';
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

  // 将Telegram主题应用到整个应用
  useEffect(() => {
    if (isInitialized && themeParams) {
      // 获取CSS变量对象
      const cssVars = getThemeCssVars();
      
      // 将CSS变量应用到根元素
      const root = document.documentElement;
      Object.entries(cssVars).forEach(([key, value]) => {
        root.style.setProperty(key, value);
      });
    }
  }, [isInitialized, themeParams, getThemeCssVars]);

  return (
    <div
      className="min-h-screen text-gray-900 dark:text-gray-100"
      style={isAvailable ? {
        backgroundColor: 'var(--tg-theme-bg-color)',
        color: 'var(--tg-theme-text-color)'
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
            color: 'var(--tg-theme-text-color)',
          }}
        >
          <p className="text-sm">
            欢迎，{userInfo.firstName} {userInfo.lastName}
            {userInfo.username ? ` (@${userInfo.username})` : ''}
          </p>
        </div>
      )}
      
      {/* 主内容区域 - 搜索页面 */}
      <SearchPage />
    </div>
  );
}

export default App;
