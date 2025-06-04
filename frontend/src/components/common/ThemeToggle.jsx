import { useState, useEffect } from 'react';
import useThemeStore from '../../store/themeStore';

/**
 * 主题切换组件
 * 支持快速切换和详细选择两种模式
 */
const ThemeToggle = ({ 
  mode = 'simple', // 'simple' | 'detailed'
  size = 'medium',  // 'small' | 'medium' | 'large'
  showLabel = true,
  className = ''
}) => {
  const {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
    getThemeDisplayName,
    getThemeIcon,
    isInitializing
  } = useThemeStore();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // 主题选项
  const themeOptions = [
    { value: 'light', label: '浅色模式', icon: '☀️', description: '适合白天使用' },
    { value: 'dark', label: '深色模式', icon: '🌙', description: '适合夜间使用' },
    { value: 'system', label: '跟随系统', icon: '💻', description: '自动跟随系统设置' }
  ];

  // 根据尺寸获取样式类
  const getSizeClasses = () => {
    const sizeMap = {
      small: {
        button: 'w-8 h-8 text-sm',
        text: 'text-xs',
        dropdown: 'text-sm'
      },
      medium: {
        button: 'w-10 h-10 text-base',
        text: 'text-sm',
        dropdown: 'text-base'
      },
      large: {
        button: 'w-12 h-12 text-lg',
        text: 'text-base',
        dropdown: 'text-lg'
      }
    };
    return sizeMap[size] || sizeMap.medium;
  };

  const sizeClasses = getSizeClasses();

  // 简单模式 - 快速切换按钮
  const SimpleToggle = () => (
    <button
      onClick={toggleTheme}
      className={`
        ${sizeClasses.button}
        flex items-center justify-center
        bg-bg-secondary hover:bg-bg-tertiary
        border border-border-primary
        rounded-lg
        transition-theme
        focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2
        ${className}
      `}
      title={`当前: ${getThemeDisplayName(theme)}, 点击切换主题`}
      disabled={isInitializing}
    >
      <span className="transition-transform duration-300 hover:scale-110">
        {getThemeIcon(resolvedTheme)}
      </span>
    </button>
  );

  // 详细模式 - 下拉选择器
  const DetailedToggle = () => (
    <div className={`relative ${className}`}>
      {/* 触发按钮 */}
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className={`
          flex items-center space-x-2 px-3 py-2
          bg-bg-secondary hover:bg-bg-tertiary
          border border-border-primary
          rounded-lg
          transition-theme
          focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2
          ${sizeClasses.dropdown}
        `}
        disabled={isInitializing}
      >
        <span>{getThemeIcon(theme)}</span>
        {showLabel && <span>{getThemeDisplayName(theme)}</span>}
        <svg 
          className={`w-4 h-4 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* 下拉菜单 */}
      {isDropdownOpen && (
        <div className="
          absolute top-full left-0 mt-1 z-50
          min-w-48
          bg-bg-primary
          border border-border-primary
          rounded-lg
          shadow-theme-lg
          overflow-hidden
        ">
          {themeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                setTheme(option.value);
                setIsDropdownOpen(false);
              }}
              className={`
                w-full px-4 py-3 text-left
                flex items-start space-x-3
                hover:bg-bg-secondary
                transition-theme
                ${theme === option.value ? 'bg-accent-primary/10 text-accent-primary' : 'text-text-primary'}
                ${sizeClasses.dropdown}
              `}
            >
              <span className="text-lg">{option.icon}</span>
              <div className="flex-1">
                <div className="font-medium">{option.label}</div>
                <div className="text-text-secondary text-xs mt-0.5">
                  {option.description}
                </div>
                {option.value === 'system' && (
                  <div className="text-text-tertiary text-xs mt-1">
                    当前系统: {getThemeDisplayName(resolvedTheme)}
                  </div>
                )}
              </div>
              {theme === option.value && (
                <svg className="w-5 h-5 text-accent-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path 
                    fillRule="evenodd" 
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" 
                    clipRule="evenodd" 
                  />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDropdownOpen && !event.target.closest('.relative')) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDropdownOpen]);

  // 键盘事件处理
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && isDropdownOpen) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isDropdownOpen]);

  // 加载状态
  if (isInitializing) {
    return (
      <div className={`
        ${sizeClasses.button}
        flex items-center justify-center
        bg-bg-secondary
        border border-border-primary
        rounded-lg
        animate-pulse
        ${className}
      `}>
        <div className="w-4 h-4 bg-text-tertiary rounded-full"></div>
      </div>
    );
  }

  return mode === 'simple' ? <SimpleToggle /> : <DetailedToggle />;
};

export default ThemeToggle; 