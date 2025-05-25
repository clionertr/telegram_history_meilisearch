import { useState, useEffect, useRef } from 'react';
import useSearchStore from '../store/searchStore';
import useTelegramSDK from '../hooks/useTelegramSDK';

/**
 * 搜索栏组件 - 阶段3重构版本
 * 实现卡片式设计和新的视觉风格
 */
function SearchBar() {
  // 从store获取状态和action
  const {
    query: storeQuery,
    setQuery,
    fetchResults,
    isLoading
  } = useSearchStore();
  
  // 使用TMA SDK钩子
  const {
    isAvailable,
    themeParams,
    triggerHapticFeedback
  } = useTelegramSDK();
  
  // 本地状态，用于控制输入框的值
  const [localQuery, setLocalQuery] = useState(storeQuery);
  
  // Refs用于直接操作DOM元素
  const inputRef = useRef(null);

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
      
      // 触发触觉反馈
      triggerHapticFeedback('impact');
    }
  };

  /**
   * 处理输入框变化
   * @param {Event} e - 输入事件
   */
  const handleInputChange = (e) => {
    setLocalQuery(e.target.value);
  };

  /**
   * 处理键盘事件
   * @param {KeyboardEvent} e - 键盘事件
   */
  const handleKeyDown = (e) => {
    // 当按下Enter键时，自动提交搜索
    if (e.key === 'Enter' && localQuery.trim() && !isLoading) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="search-bar-container">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-wrapper">
          {/* 搜索图标 */}
          <div className="search-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M21 21L16.514 16.506M19 10.5C19 15.194 15.194 19 10.5 19C5.806 19 2 15.194 2 10.5C2 5.806 5.806 2 10.5 2C15.194 2 19 5.806 19 10.5Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          
          {/* 搜索输入框 */}
          <input
            ref={inputRef}
            type="text"
            value={localQuery}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="输入关键词搜索..."
            aria-label="搜索关键词"
            className="search-input"
            disabled={isLoading}
          />
        </div>

        {/* 搜索按钮 - 总是显示，变小并放在右侧 */}
        <button
          type="submit"
          className="search-button-compact"
          disabled={isLoading || !localQuery.trim()}
          aria-label="搜索"
        >
          {isLoading ? (
            <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.3"/>
              <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"/>
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M21 21L16.514 16.506M19 10.5C19 15.194 15.194 19 10.5 19C5.806 19 2 15.194 2 10.5C2 5.806 5.806 2 10.5 2C15.194 2 19 5.806 19 10.5Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </button>
      </form>

      {/* 在Telegram Mini App中的提示信息 */}
      {isAvailable && (
        <div className="telegram-hint">
          {localQuery.trim()
            ? "点击搜索按钮或下方主按钮开始搜索"
            : "请输入关键词后点击搜索按钮"}
        </div>
      )}
    </div>
  );
}

export default SearchBar;