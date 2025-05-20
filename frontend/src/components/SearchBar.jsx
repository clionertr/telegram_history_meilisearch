import { useState, useEffect } from 'react';
import useSearchStore from '../store/searchStore';

/**
 * 搜索栏组件
 * 包含搜索输入框和提交按钮
 */
function SearchBar() {
  // 从store获取状态和action
  const { 
    query: storeQuery, 
    setQuery, 
    fetchResults, 
    isLoading 
  } = useSearchStore();
  
  // 本地状态，用于控制输入框的值
  const [localQuery, setLocalQuery] = useState(storeQuery);

  // 当store中的query改变时，更新本地状态
  useEffect(() => {
    setLocalQuery(storeQuery);
  }, [storeQuery]);

  /**
   * 处理搜索提交
   * @param {Event} e - 表单提交事件
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    // 更新store中的query，并触发搜索
    if (localQuery.trim()) {
      setQuery(localQuery);
      fetchResults(localQuery, 1); // 重置到第一页
    }
  };

  /**
   * 处理输入框变化
   * @param {Event} e - 输入事件
   */
  const handleInputChange = (e) => {
    setLocalQuery(e.target.value);
  };

  // 检查是否在Telegram Mini App环境中
  const isTelegramMiniApp = typeof window !== 'undefined' && window.Telegram?.WebApp;

  return (
    <form onSubmit={handleSubmit} className="w-full mb-6">
      <div className="flex">
        <input
          type="text"
          value={localQuery}
          onChange={handleInputChange}
          placeholder="输入关键词搜索..."
          aria-label="搜索关键词"
          className="flex-grow px-4 py-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        
        {/* 非Telegram环境下显示搜索按钮 */}
        {!isTelegramMiniApp && (
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
            disabled={isLoading || !localQuery.trim()}
          >
            {isLoading ? '搜索中...' : '搜索'}
          </button>
        )}
      </div>

      {/* 在Telegram Mini App中，使用MainButton触发搜索 */}
      {isTelegramMiniApp && (
        <div className="mt-2 text-sm text-gray-500">
          点击下方主按钮开始搜索
        </div>
      )}
    </form>
  );
}

export default SearchBar;