import { useEffect } from 'react';
import SearchBar from '../components/SearchBar';
import ResultsList from '../components/ResultsList';
import useSearchStore from '../store/searchStore';

/**
 * 搜索页面组件
 * 作为主要的搜索界面，组合搜索栏和结果列表
 */
function SearchPage() {
  const { query, fetchResults } = useSearchStore();

  // 初始化Telegram Mini App的MainButton
  useEffect(() => {
    // 检查是否在Telegram Mini App环境中
    const isTelegramMiniApp = window.Telegram?.WebApp;
    
    if (isTelegramMiniApp) {
      try {
        const tg = window.Telegram.WebApp;
        
        // 设置主按钮文本
        tg.MainButton.setText('开始搜索');
        
        // 根据查询词状态决定主按钮是否可见
        if (query.trim()) {
          tg.MainButton.show();
        } else {
          tg.MainButton.hide();
        }
        
        // 设置主按钮点击事件
        const handleMainButtonClick = () => {
          if (query.trim()) {
            fetchResults();
          }
        };
        
        tg.MainButton.onClick(handleMainButtonClick);
        
        // 清理函数
        return () => {
          tg.MainButton.offClick(handleMainButtonClick);
        };
      } catch (error) {
        console.error('Telegram Mini App SDK初始化失败:', error);
      }
    }
  }, [query, fetchResults]);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-teal-400 bg-clip-text text-transparent">
          Telegram 中文历史消息搜索
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          在您的Telegram历史消息中快速查找信息
        </p>
      </header>

      <main>
        {/* 搜索栏 */}
        <SearchBar />
        
        {/* 搜索结果列表 */}
        <ResultsList />
      </main>
    </div>
  );
}

export default SearchPage;