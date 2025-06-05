import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSessionsStore } from '../store/sessionsStore.js';

/**
 * 会话搜索栏组件
 * 提供实时搜索、类型筛选和搜索建议功能
 */
const SessionSearchBar = () => {
  const {
    searchQuery,
    searchTypeFilter,
    isSearchMode,
    isSearching,
    searchError,
    searchSessions,
    exitSearchMode,
    setTypeFilter,
    getSearchSuggestions,
    clearSearchError
  } = useSessionsStore();

  // 本地状态
  const [inputValue, setInputValue] = useState(searchQuery);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);

  // 引用
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const searchTimeoutRef = useRef(null);

  // 防抖搜索
  const debouncedSearch = useCallback((query, typeFilter) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      if (query.trim()) {
        searchSessions(query, typeFilter, 1);
      } else {
        exitSearchMode();
      }
    }, 300); // 300ms 防抖
  }, [searchSessions, exitSearchMode]);

  // 输入变化处理
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInputValue(value);

    // 获取搜索建议
    const newSuggestions = getSearchSuggestions(value);
    setSuggestions(newSuggestions);
    setShowSuggestions(value.length > 0 && newSuggestions.length > 0);
    setSelectedSuggestionIndex(-1);

    // 执行防抖搜索
    if (value.trim()) {
      debouncedSearch(value, searchTypeFilter);
    } else {
      exitSearchMode();
      setShowSuggestions(false);
    }
  };

  // 类型筛选变化处理
  const handleTypeFilterChange = (e) => {
    const newTypeFilter = e.target.value;
    setTypeFilter(newTypeFilter);
    
    // 如果当前有搜索查询，重新执行搜索
    if (inputValue.trim()) {
      debouncedSearch(inputValue, newTypeFilter);
    }
  };

  // 键盘事件处理
  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Escape') {
        handleClear();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          handleSuggestionClick(suggestions[selectedSuggestionIndex]);
        } else if (inputValue.trim()) {
          setShowSuggestions(false);
          debouncedSearch(inputValue, searchTypeFilter);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  // 建议点击处理
  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion);
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    debouncedSearch(suggestion, searchTypeFilter);
    inputRef.current?.blur();
  };

  // 清空搜索
  const handleClear = () => {
    setInputValue('');
    setShowSuggestions(false);
    setSuggestions([]);
    setSelectedSuggestionIndex(-1);
    exitSearchMode();
    clearSearchError();
    inputRef.current?.focus();
  };

  // 同步外部状态到本地状态
  useEffect(() => {
    if (searchQuery !== inputValue && !isSearching) {
      setInputValue(searchQuery);
    }
  }, [searchQuery, isSearching]);

  // 点击外部关闭建议
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target) &&
          inputRef.current && !inputRef.current.contains(event.target)) {
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="relative mb-6">
      {/* 搜索输入区域 */}
      <div className="flex gap-3">
        {/* 搜索输入框 */}
        <div className="relative flex-1">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => {
                if (inputValue && suggestions.length > 0) {
                  setShowSuggestions(true);
                }
              }}
              placeholder="搜索会话名称或ID..."
              className="w-full px-4 py-3 pl-12 pr-10 border border-border-primary rounded-lg bg-bg-secondary text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-theme"
            />
            
            {/* 搜索图标 */}
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
              {isSearching ? (
                <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-5 h-5 text-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              )}
            </div>

            {/* 清空按钮 */}
            {(inputValue || isSearchMode) && (
              <button
                onClick={handleClear}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 text-text-tertiary hover:text-text-secondary transition-theme"
                type="button"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* 搜索建议 */}
          {showSuggestions && suggestions.length > 0 && (
            <div
              ref={suggestionsRef}
              className="absolute z-50 w-full mt-1 bg-bg-secondary border border-border-primary rounded-lg shadow-theme-lg max-h-60 overflow-y-auto"
            >
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className={`w-full px-4 py-2 text-left hover:bg-bg-tertiary transition-theme ${
                    index === selectedSuggestionIndex ? 'bg-bg-tertiary' : ''
                  }`}
                >
                  <span className="text-text-primary">{suggestion}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 类型筛选 */}
        <select
          value={searchTypeFilter}
          onChange={handleTypeFilterChange}
          className="px-4 py-3 border border-border-primary rounded-lg bg-bg-secondary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-theme min-w-[120px]"
        >
          <option value="">所有类型</option>
          <option value="user">👤 用户</option>
          <option value="group">👥 群组</option>
          <option value="channel">📢 频道</option>
        </select>
      </div>

      {/* 搜索状态指示器 */}
      {isSearchMode && (
        <div className="mt-3 flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <span className="text-primary">搜索模式</span>
            {searchQuery && (
              <span className="text-text-secondary">
                关键词: <span className="font-medium text-text-primary">"{searchQuery}"</span>
              </span>
            )}
            {searchTypeFilter && (
              <span className="text-text-secondary">
                类型: <span className="font-medium text-text-primary">
                  {searchTypeFilter === 'user' ? '👤 用户' : 
                   searchTypeFilter === 'group' ? '👥 群组' : 
                   searchTypeFilter === 'channel' ? '📢 频道' : searchTypeFilter}
                </span>
              </span>
            )}
          </div>
          
          <button
            onClick={handleClear}
            className="text-text-tertiary hover:text-text-primary transition-theme"
          >
            退出搜索
          </button>
        </div>
      )}

      {/* 搜索错误显示 */}
      {searchError && (
        <div className="mt-3 p-3 bg-error/10 border border-error/20 rounded-lg">
          <div className="flex items-center gap-2 text-error">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm">{searchError}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionSearchBar; 