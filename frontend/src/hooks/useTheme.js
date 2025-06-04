import { useEffect, useCallback } from 'react';
import useThemeStore from '../store/themeStore';

/**
 * 主题管理Hook
 * 提供主题初始化和便捷的主题操作方法
 */
const useTheme = () => {
  const {
    theme,
    resolvedTheme,
    isInitializing,
    setTheme,
    toggleTheme,
    initializeTheme,
    setupSystemThemeListener,
    getThemeDisplayName,
    getThemeIcon
  } = useThemeStore();

  // 初始化主题系统
  useEffect(() => {
    // 初始化主题
    initializeTheme();
    
    // 设置系统主题监听器
    const cleanup = setupSystemThemeListener();
    
    // 清理函数
    return cleanup;
  }, [initializeTheme, setupSystemThemeListener]);

  // 检查是否为深色主题
  const isDark = useCallback(() => {
    return resolvedTheme === 'dark';
  }, [resolvedTheme]);

  // 检查是否为浅色主题
  const isLight = useCallback(() => {
    return resolvedTheme === 'light';
  }, [resolvedTheme]);

  // 检查是否为系统主题模式
  const isSystemMode = useCallback(() => {
    return theme === 'system';
  }, [theme]);

  // 切换到浅色主题
  const setLightTheme = useCallback(() => {
    setTheme('light');
  }, [setTheme]);

  // 切换到深色主题
  const setDarkTheme = useCallback(() => {
    setTheme('dark');
  }, [setTheme]);

  // 切换到系统主题
  const setSystemTheme = useCallback(() => {
    setTheme('system');
  }, [setTheme]);

  // 获取主题相关的CSS类
  const getThemeClasses = useCallback((config = {}) => {
    const {
      lightClasses = '',
      darkClasses = '',
      baseClasses = ''
    } = config;

    const base = baseClasses;
    const themeSpecific = isDark() ? darkClasses : lightClasses;
    
    return `${base} ${themeSpecific}`.trim();
  }, [isDark]);

  // 获取当前主题的颜色值
  const getThemeColors = useCallback(() => {
    if (typeof window === 'undefined') {
      return {};
    }

    const root = document.documentElement;
    const style = getComputedStyle(root);

    return {
      // 背景色
      bgPrimary: style.getPropertyValue('--color-bg-primary').trim(),
      bgSecondary: style.getPropertyValue('--color-bg-secondary').trim(),
      bgTertiary: style.getPropertyValue('--color-bg-tertiary').trim(),
      
      // 文字色
      textPrimary: style.getPropertyValue('--color-text-primary').trim(),
      textSecondary: style.getPropertyValue('--color-text-secondary').trim(),
      textTertiary: style.getPropertyValue('--color-text-tertiary').trim(),
      
      // 边框色
      borderPrimary: style.getPropertyValue('--color-border-primary').trim(),
      borderSecondary: style.getPropertyValue('--color-border-secondary').trim(),
      
      // 主题色
      accentPrimary: style.getPropertyValue('--color-accent-primary').trim(),
      accentSecondary: style.getPropertyValue('--color-accent-secondary').trim(),
      accentHover: style.getPropertyValue('--color-accent-hover').trim(),
    };
  }, []);

  // 创建主题感知的样式对象
  const createThemeStyles = useCallback((lightStyles = {}, darkStyles = {}) => {
    return isDark() ? { ...lightStyles, ...darkStyles } : lightStyles;
  }, [isDark]);

  return {
    // 基础状态
    theme,
    resolvedTheme,
    isInitializing,
    
    // 状态检查
    isDark: isDark(),
    isLight: isLight(),
    isSystemMode: isSystemMode(),
    
    // 主题操作
    setTheme,
    toggleTheme,
    setLightTheme,
    setDarkTheme,
    setSystemTheme,
    
    // 工具方法
    getThemeDisplayName,
    getThemeIcon,
    getThemeClasses,
    getThemeColors,
    createThemeStyles,
    
    // 函数版本（用于回调）
    isDarkMode: isDark,
    isLightMode: isLight,
    isSystemModeActive: isSystemMode
  };
};

export default useTheme; 