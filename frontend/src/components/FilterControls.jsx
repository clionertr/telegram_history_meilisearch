import { useState, useEffect } from 'react';
import useSearchStore from '../store/searchStore';
import useTelegramSDK from '../hooks/useTelegramSDK';

/**
 * 筛选控件组件 - 阶段3重构版本
 * 实现新的卡片式设计和现代化筛选界面
 */
function FilterControls() {
  // 从store获取状态和action
  const { filters, setFilters, fetchResults, isLoading } = useSearchStore();
  
  // 使用TMA SDK钩子
  const { triggerHapticFeedback } = useTelegramSDK();

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
   * 处理展开/折叠切换
   */
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
    triggerHapticFeedback('light');
  };

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
    triggerHapticFeedback('selection');
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
    triggerHapticFeedback('impact');
  };

  // 是否有任何筛选条件被应用
  const hasActiveFilters = filters.chat_type?.length > 0 || filters.date_from || filters.date_to;

  // 聊天类型选项
  const chatTypeOptions = [
    { value: 'private', label: '私聊', icon: '👤' },
    { value: 'group', label: '群组', icon: '👥' },
    { value: 'supergroup', label: '超级群组', icon: '🏢' },
    { value: 'channel', label: '频道', icon: '📢' }
  ];

  return (
    <div className="filter-controls">
      {/* 筛选条件展开/折叠按钮 */}
      <div 
        className="filter-header"
        onClick={toggleExpanded}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleExpanded();
          }
        }}
      >
        <div className="filter-title">
          <div className="filter-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M22 3H2L10 12.46V19L14 21V12.46L22 3Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <span>筛选条件</span>
          {hasActiveFilters && (
            <div className="filter-badge">
              {(filters.chat_type?.length || 0) + (filters.date_from || filters.date_to ? 1 : 0)}
            </div>
          )}
        </div>
        
        <div className={`filter-expand-icon ${isExpanded ? 'expanded' : ''}`}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M6 9L12 15L18 9"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      {/* 筛选条件内容 */}
      {isExpanded && (
        <div className="filter-content">
          {/* 聊天类型筛选 */}
          <div className="filter-section">
            <h4 className="filter-section-title">聊天类型</h4>
            <div className="chat-type-grid">
              {chatTypeOptions.map(option => (
                <label key={option.value} className="chat-type-option">
                  <input
                    type="checkbox"
                    checked={localFilters.chat_type.includes(option.value)}
                    onChange={(e) => handleChatTypeChange(option.value, e.target.checked)}
                    className="chat-type-checkbox"
                  />
                  <div className="chat-type-content">
                    <span className="chat-type-icon">{option.icon}</span>
                    <span className="chat-type-label">{option.label}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 时间范围筛选 */}
          <div className="filter-section">
            <h4 className="filter-section-title">时间范围</h4>
            <div className="date-range">
              <div className="date-input-group">
                <label className="date-label">开始日期</label>
                <input
                  type="date"
                  value={localFilters.date_from}
                  onChange={(e) => handleDateChange('date_from', e.target.value)}
                  className="date-input"
                  disabled={isLoading}
                />
              </div>
              <div className="date-separator">至</div>
              <div className="date-input-group">
                <label className="date-label">结束日期</label>
                <input
                  type="date"
                  value={localFilters.date_to}
                  onChange={(e) => handleDateChange('date_to', e.target.value)}
                  className="date-input"
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>

          {/* 操作按钮 */}
          {hasActiveFilters && (
            <div className="filter-actions">
              <button
                onClick={clearFilters}
                className="clear-filters-btn"
                disabled={isLoading}
              >
                清空筛选
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FilterControls;