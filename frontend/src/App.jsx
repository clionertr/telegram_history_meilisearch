import { useState, useEffect } from 'react';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

function App() {
  const [count, setCount] = useState(0);
  const [telegramUserInfo, setTelegramUserInfo] = useState(null);

  // 尝试初始化Telegram Mini App SDK（如果在Telegram环境中运行）
  useEffect(() => {
    // 检查是否在Telegram Mini App环境中
    const isTelegramMiniApp = window.Telegram?.WebApp;
    
    if (isTelegramMiniApp) {
      try {
        // 初始化Telegram Mini App SDK
        const tg = window.Telegram.WebApp;
        tg.ready();

        // 获取用户信息
        setTelegramUserInfo({
          username: tg.initDataUnsafe?.user?.username || '未知用户',
          firstName: tg.initDataUnsafe?.user?.first_name || '',
          lastName: tg.initDataUnsafe?.user?.last_name || '',
        });

        // 设置主按钮
        tg.MainButton.setText('开始搜索');
        tg.MainButton.onClick(() => {
          // MainButton点击逻辑
          console.log('开始搜索');
          // 这里将来会实现搜索逻辑
        });
      } catch (error) {
        console.error('Telegram Mini App SDK初始化失败:', error);
      }
    }
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8 text-center">
      <div className="flex justify-center mb-6 space-x-6">
        <a href="https://vite.dev" target="_blank" className="hover:scale-110 transition-transform">
          <img src={viteLogo} className="h-24 p-2" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" className="hover:scale-110 transition-transform">
          <img src={reactLogo} className="h-24 p-2 animate-spin-slow" alt="React logo" />
        </a>
      </div>
      
      <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-500 to-teal-400 bg-clip-text text-transparent mb-8">
        Telegram 中文历史消息搜索
      </h1>
      
      {telegramUserInfo && (
        <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-4 mb-8">
          <p className="text-lg">
            欢迎，{telegramUserInfo.firstName} {telegramUserInfo.lastName}
            {telegramUserInfo.username ? ` (@${telegramUserInfo.username})` : ''}
          </p>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-8">
        <button 
          onClick={() => setCount((count) => count + 1)}
          className="bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-2 px-6 rounded-lg transition-colors"
        >
          计数: {count}
        </button>
        <p className="mt-4 text-gray-600 dark:text-gray-300">
          编辑 <code className="font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">src/App.jsx</code> 并保存以测试HMR
        </p>
      </div>

      <p className="text-gray-500 dark:text-gray-400">
        点击Vite和React的logo以了解更多信息
      </p>
      
      <div className="mt-8 p-4 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg text-left">
        <h2 className="text-xl font-semibold mb-2">项目初始化完成:</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>React + Vite 安装成功</li>
          <li>Tailwind CSS 配置完成</li>
          <li>Telegram Mini App SDK 集成</li>
          <li>Zustand 状态管理准备就绪</li>
          <li>ESLint + Prettier 配置完成</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
