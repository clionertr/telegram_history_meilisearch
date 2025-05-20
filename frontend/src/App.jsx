import { useState, useEffect } from 'react';
import SearchPage from './pages/SearchPage';
import './App.css';

/**
 * 应用主组件
 */
function App() {
  const [telegramUserInfo, setTelegramUserInfo] = useState(null);

  // 初始化Telegram Mini App SDK（如果在Telegram环境中运行）
  useEffect(() => {
    // 检查是否在Telegram Mini App环境中
    const isTelegramMiniApp = window.Telegram?.WebApp;
    
    if (isTelegramMiniApp) {
      try {
        // 初始化Telegram Mini App SDK
        const tg = window.Telegram.WebApp;
        tg.ready();
        
        // 扩展视图（如果可能）
        if (tg.expand) {
          tg.expand();
        }

        // 获取用户信息
        setTelegramUserInfo({
          username: tg.initDataUnsafe?.user?.username || '未知用户',
          firstName: tg.initDataUnsafe?.user?.first_name || '',
          lastName: tg.initDataUnsafe?.user?.last_name || '',
        });
      } catch (error) {
        console.error('Telegram Mini App SDK初始化失败:', error);
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* 用户信息显示区域 */}
      {telegramUserInfo && (
        <div className="bg-blue-50 dark:bg-blue-900/30 p-2 text-center">
          <p className="text-sm">
            欢迎，{telegramUserInfo.firstName} {telegramUserInfo.lastName}
            {telegramUserInfo.username ? ` (@${telegramUserInfo.username})` : ''}
          </p>
        </div>
      )}
      
      {/* 主内容区域 - 搜索页面 */}
      <SearchPage />
    </div>
  );
}

export default App;
