import { useState, useEffect } from 'react';
import useSearchStore from '../store/searchStore';
import useTelegramSDK from '../hooks/useTelegramSDK';

/**
 * 筛选控件组件
 * 允许用户按消息来源类别和时间段筛选搜索结果
 */
function FilterControls() {
  // 从store获取状态和action
  const { filters, setFilters, fetchResults, isLoading } = useSearchStore();
  
  // 使用TMA SDK钩子
  const { isAvailable, themeParams } = useTelegramSDK();

  // 计算默认日期
  const getDefaultDates = () => {
    // 结束日期默认为明天
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const defaultDateTo = tomorrow.toISOString().split('T')[0];
    
    // 开始日期默认为三个月前
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
    const defaultDateFrom = threeMonthsAgo.toISOString().split('T')[0];
    
    return { defaultDateFrom, defaultDateTo };
  };
  
  const { defaultDateFrom, defaultDateTo } = getDefaultDates();

  // 本地状态，用于控制UI
  const [isExpanded, setIsExpanded] = useState(false);
  const [localFilters, setLocalFilters] = useState({
    chat_type: filters.chat_type || [],
    date_from: filters.date_from
      ? new Date(filters.date_from * 1000).toISOString().split('T')[0]
      : defaultDateFrom,
    date_to: filters.date_to
      ? new Date(filters.date_to * 1000).toISOString().split('T')[0]
      : defaultDateTo
  });

  // 当store中的filters改变时，更新本地状态
  // 初始化时应用默认筛选条件（如果没有已有筛选）
  useEffect(() => {
    if (!filters.date_from && !filters.date_to && (!filters.chat_type || filters.chat_type.length === 0)) {
      // 将日期字符串转换为Unix时间戳（秒级）
      const dateFromTimestamp = Math.floor(new Date(defaultDateFrom).getTime() / 1000);
      const dateToTimestamp = Math.floor(new Date(defaultDateTo + 'T23:59:59').getTime() / 1000);
      
      // 更新store中的filters（但不自动搜索，等用户主动搜索）
      setFilters({
        chat_type: [],
        date_from: dateFromTimestamp,
        date_to: dateToTimestamp
      });
    }
  }, []);  // 仅在组件挂载时运行一次

  // 当store中的filters改变时，更新本地状态
  useEffect(() => {
    setLocalFilters({
      chat_type: filters.chat_type || [],
      date_from: filters.date_from ? new Date(filters.date_from * 1000).toISOString().split('T')[0] : defaultDateFrom,
      date_to: filters.date_to ? new Date(filters.date_to * 1000).toISOString().split('T')[0] : defaultDateTo
    });
  }, [filters]);

  /**
   * 处理聊天类型复选框变更
   * @param {string} type - 聊天类型
   * @param {boolean} checked - 是否选中
   */
  const handleChatTypeChange = (type, checked) => {
    const updatedChatTypes = checked
      ? [...localFilters.chat_type, type]
      : localFilters.chat_type.filter(t => t !== type);
    
    const updatedFilters = {
      ...localFilters,
      chat_type: updatedChatTypes
    };
    
    setLocalFilters(updatedFilters);
    
    // 自动应用筛选
    applyFiltersWithValues(updatedFilters);
  };

  /**
   * 处理日期变更
   * @param {string} field - 字段名 (date_from 或 date_to)
   * @param {string} value - 日期字符串 (YYYY-MM-DD)
   */
  const handleDateChange = (field, value) => {
    const updatedFilters = {
      ...localFilters,
      [field]: value
    };
    
    setLocalFilters(updatedFilters);
    
    // 自动应用筛选
    applyFiltersWithValues(updatedFilters);
  };

  /**
   * 使用给定的筛选值应用筛选条件
   */
  const applyFiltersWithValues = (filterValues) => {
    // 将日期字符串转换为Unix时间戳（秒级）
    const dateFromTimestamp = filterValues.date_from
      ? Math.floor(new Date(filterValues.date_from).getTime() / 1000)
      : null;
    
    const dateToTimestamp = filterValues.date_to
      ? Math.floor(new Date(filterValues.date_to + 'T23:59:59').getTime() / 1000) // 设置为当天最后一秒
      : null;
    
    // 准备筛选条件对象
    const newFilters = {
      chat_type: filterValues.chat_type.length > 0 ? filterValues.chat_type : [],
      date_from: dateFromTimestamp,
      date_to: dateToTimestamp
    };
    
    // 更新store中的filters并触发搜索
    setFilters(newFilters);
    fetchResults(undefined, 1); // 重置到第一页，使用当前的查询词
  };
  
  /**
   * 应用当前本地筛选条件
   */
  const applyFilters = () => {
    applyFiltersWithValues(localFilters);
  };

  /**
   * 清空所有筛选条件
   */
  const clearFilters = () => {
    setLocalFilters({
      chat_type: [],
      date_from: '',
      date_to: ''
    });
    
    setFilters({
      chat_type: [],
      date_from: null,
      date_to: null
    });
    
    fetchResults(undefined, 1); // 重置到第一页，使用当前的查询词
  };

  // 根据Telegram主题获取样式
  const containerStyle = isAvailable && themeParams
    ? { borderColor: themeParams.hint_color }
    : {};
  
  const textStyle = isAvailable && themeParams
    ? { color: themeParams.text_color }
    : {};
  
  const hintTextStyle = isAvailable && themeParams
    ? { color: themeParams.hint_color }
    : { color: 'rgb(107 114 128)' };
  
  const buttonStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.button_color,
    color: themeParams.button_text_color,
  } : {
    backgroundColor: 'rgb(59 130 246)',
    color: 'white',
  };

  const secondaryButtonStyle = isAvailable && themeParams ? {
    borderColor: themeParams.hint_color,
    color: themeParams.text_color,
  } : {};

  const inputStyle = isAvailable && themeParams ? {
    borderColor: themeParams.hint_color,
    backgroundColor: themeParams.secondary_bg_color,
    color: themeParams.text_color,
  } : {};

  // 是否有任何筛选条件被应用
  const hasActiveFilters = filters.chat_type?.length > 0 || filters.date_from || filters.date_to;

  return (
    <div className="w-full mb-4">
      {/* 筛选条件展开/折叠按钮 */}
      <div 
        className="flex justify-between items-center px-4 py-2 mb-2 cursor-pointer rounded-lg border border-gray-300"
        style={containerStyle}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center" style={textStyle}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          <span className="font-medium">筛选条件</span>
          {hasActiveFilters && (
            <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">
              已筛选
            </span>
          )}
        </div>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className={`h-5 w-5 transition-transform ${isExpanded ? 'transform rotate-180' : ''}`} 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
          style={textStyle}
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* 筛选控件 - 展开时显示 */}
      {isExpanded && (
        <div className="border rounded-lg p-4 mb-4" style={containerStyle}>
          {/* 消息来源类别筛选 */}
          <div className="mb-4">
            <h3 className="font-medium mb-2" style={textStyle}>按消息来源筛选:</h3>
            <div className="flex flex-wrap gap-4">
              {['user', 'group', 'channel'].map(type => (
                <label key={type} className="flex items-center cursor-pointer" style={textStyle}>
                  <input
                    type="checkbox"
                    className="mr-2 h-4 w-4"
                    checked={localFilters.chat_type.includes(type)}
                    onChange={e => handleChatTypeChange(type, e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>{type === 'user' ? '私聊' : type === 'group' ? '群组' : '频道'}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 时间段筛选 */}
          <div className="mb-4">
            <h3 className="font-medium mb-2" style={textStyle}>按时间筛选:</h3>
            <div className="flex flex-wrap gap-2 sm:gap-4">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <label style={textStyle}>开始日期:</label>
                <input
                  type="date"
                  className="px-2 py-1 border rounded"
                  style={inputStyle}
                  value={localFilters.date_from}
                  max={localFilters.date_to || undefined}
                  onChange={e => handleDateChange('date_from', e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <label style={textStyle}>结束日期:</label>
                <input
                  type="date"
                  className="px-2 py-1 border rounded"
                  style={inputStyle}
                  value={localFilters.date_to}
                  min={localFilters.date_from || undefined}
                  onChange={e => handleDateChange('date_to', e.target.value)}
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          {/* 筛选按钮 */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={clearFilters}
              className="px-4 py-2 border rounded-lg focus:outline-none disabled:opacity-50"
              style={secondaryButtonStyle}
              disabled={isLoading}
            >
              清空筛选
            </button>
          </div>
          
          {/* 提示文本 */}
          <div className="mt-2 text-xs" style={hintTextStyle}>
            提示: 筛选条件会自动应用，不选择任何筛选条件将搜索所有类型和时间段
          </div>
        </div>
      )}
      
      {/* 简洁显示当前筛选条件状态 - 折叠时显示 */}
      {!isExpanded && hasActiveFilters && (
        <div className="px-4 py-2 text-sm" style={hintTextStyle}>
          当前筛选: 
          {filters.chat_type?.length > 0 && (
            <span className="mx-1">
              {filters.chat_type.map(t => t === 'user' ? '私聊' : t === 'group' ? '群组' : '频道').join(', ')}
            </span>
          )}
          {(filters.date_from || filters.date_to) && (
            <span className="mx-1">
              {filters.date_from ? new Date(filters.date_from * 1000).toLocaleDateString() : ''}
              {filters.date_from && filters.date_to ? ' 至 ' : ''}
              {filters.date_to ? new Date(filters.date_to * 1000).toLocaleDateString() : ''}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default FilterControls;