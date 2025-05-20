import { useState, useEffect, useRef } from 'react';
import useSearchStore from '../store/searchStore';
import useTelegramSDK from '../hooks/useTelegramSDK';

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
  const buttonRef = useRef(null);

  // 当store中的query改变时，更新本地状态
  useEffect(() => {
    setLocalQuery(storeQuery);
  }, [storeQuery]);

  // 应用Telegram主题到输入框和按钮
  useEffect(() => {
    if (isAvailable && themeParams && inputRef.current) {
      // 应用输入框样式
      inputRef.current.style.borderColor = themeParams.hint_color;
      inputRef.current.style.backgroundColor = themeParams.secondary_bg_color;
      inputRef.current.style.color = themeParams.text_color;
    }
    
    if (isAvailable && themeParams && buttonRef.current) {
      // 应用按钮样式
      buttonRef.current.style.backgroundColor = themeParams.button_color;
      buttonRef.current.style.color = themeParams.button_text_color;
    }
  }, [isAvailable, themeParams]);

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
      
      // 在非TMA环境下或按钮点击时触发触觉反馈
      if (!isAvailable || e.type === 'click') {
        triggerHapticFeedback('impact');
      }
    }
  };

  /**
   * 处理输入框变化
   * @param {Event} e - 输入事件
   */
  const handleInputChange = (e) => {
    setLocalQuery(e.target.value);
  };

  // 根据是否在Telegram环境中确定提示文本颜色
  const hintTextStyle = isAvailable && themeParams
    ? { color: themeParams.hint_color }
    : { color: 'rgb(107 114 128)' };

  return (
    <form onSubmit={handleSubmit} className="w-full mb-6">
      <div className="flex">
        <input
          ref={inputRef}
          type="text"
          value={localQuery}
          onChange={handleInputChange}
          placeholder="输入关键词搜索..."
          aria-label="搜索关键词"
          className="flex-grow px-4 py-2 border rounded-l-lg focus:outline-none"
          style={isAvailable && themeParams ? {
            border: `1px solid ${themeParams.hint_color}`,
            backgroundColor: themeParams.secondary_bg_color,
            color: themeParams.text_color,
          } : {}}
          disabled={isLoading}
        />
        
        {/* 非Telegram环境下显示搜索按钮 */}
        {!isAvailable && (
          <button
            ref={buttonRef}
            type="submit"
            className="px-4 py-2 text-white rounded-r-lg focus:outline-none disabled:opacity-50"
            style={isAvailable && themeParams ? {
              backgroundColor: themeParams.button_color,
              color: themeParams.button_text_color,
            } : {
              backgroundColor: 'rgb(59 130 246)',
              color: 'white',
            }}
            disabled={isLoading || !localQuery.trim()}
          >
            {isLoading ? '搜索中...' : '搜索'}
          </button>
        )}
      </div>

      {/* 在Telegram Mini App中，使用MainButton触发搜索 */}
      {isAvailable && (
        <div className="mt-2 text-sm" style={hintTextStyle}>
          {localQuery.trim()
            ? "点击下方主按钮开始搜索"
            : "请输入关键词后使用主按钮搜索"}
        </div>
      )}
    </form>
  );
}

export default SearchBar;