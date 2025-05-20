/**
 * TMA SDK钩子 - 封装Telegram Mini App SDK功能
 */
import { useEffect, useState, useCallback } from 'react';
import WebApp from '@telegram-apps/sdk';

/**
 * 使用Telegram SDK的自定义钩子
 * 封装TMA SDK的核心功能，包括初始化、用户信息获取、主题颜色、MainButton管理等
 */
export const useTelegramSDK = () => {
  // 状态
  const [isInitialized, setIsInitialized] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [themeParams, setThemeParams] = useState(null);
  const [error, setError] = useState(null);

  // 初始化TMA SDK
  useEffect(() => {
    try {
      // 初始化
      WebApp.ready();
      
      // 扩展视图（如果可能）
      if (WebApp.isExpanded !== true) {
        WebApp.expand();
      }
      
      // 获取用户信息
      if (WebApp.initDataUnsafe?.user) {
        setUserInfo({
          id: WebApp.initDataUnsafe.user.id,
          username: WebApp.initDataUnsafe.user.username || '',
          firstName: WebApp.initDataUnsafe.user.first_name || '',
          lastName: WebApp.initDataUnsafe.user.last_name || '',
          languageCode: WebApp.initDataUnsafe.user.language_code || 'zh',
        });
      }
      
      // 获取主题参数
      setThemeParams({
        bg_color: WebApp.themeParams.bg_color || '#ffffff',
        text_color: WebApp.themeParams.text_color || '#000000',
        hint_color: WebApp.themeParams.hint_color || '#999999',
        link_color: WebApp.themeParams.link_color || '#2481cc',
        button_color: WebApp.themeParams.button_color || '#2481cc',
        button_text_color: WebApp.themeParams.button_text_color || '#ffffff',
        secondary_bg_color: WebApp.themeParams.secondary_bg_color || '#f0f0f0',
      });
      
      setIsInitialized(true);
    } catch (err) {
      console.error('TMA SDK初始化失败:', err);
      setError(err.message || '初始化失败');
    }
  }, []);

  /**
   * 设置MainButton的文本
   * @param {string} text - 按钮文本
   */
  const setMainButtonText = useCallback((text) => {
    if (!isInitialized) return;
    try {
      WebApp.MainButton.setText(text);
    } catch (err) {
      console.error('设置MainButton文本失败:', err);
    }
  }, [isInitialized]);

  /**
   * 显示MainButton
   * @param {string} [text] - 可选的按钮文本
   */
  const showMainButton = useCallback((text) => {
    if (!isInitialized) return;
    try {
      if (text) {
        WebApp.MainButton.setText(text);
      }
      WebApp.MainButton.show();
    } catch (err) {
      console.error('显示MainButton失败:', err);
    }
  }, [isInitialized]);

  /**
   * 隐藏MainButton
   */
  const hideMainButton = useCallback(() => {
    if (!isInitialized) return;
    try {
      WebApp.MainButton.hide();
    } catch (err) {
      console.error('隐藏MainButton失败:', err);
    }
  }, [isInitialized]);

  /**
   * 设置MainButton点击事件
   * @param {Function} callback - 点击回调函数
   * @returns {Function} 清理函数，用于移除事件监听器
   */
  const setMainButtonClickHandler = useCallback((callback) => {
    if (!isInitialized || !callback) return () => {};
    
    try {
      WebApp.MainButton.onClick(callback);
      return () => WebApp.MainButton.offClick(callback);
    } catch (err) {
      console.error('设置MainButton点击事件失败:', err);
      return () => {};
    }
  }, [isInitialized]);

  /**
   * 触发触觉反馈（如果支持）
   * @param {string} style - 反馈类型：'impact', 'notification', 'selection'
   */
  const triggerHapticFeedback = useCallback((style = 'impact') => {
    if (!isInitialized) return;
    
    try {
      // 检查是否支持触觉反馈
      if (WebApp.HapticFeedback) {
        switch (style) {
          case 'impact':
            WebApp.HapticFeedback.impactOccurred('medium');
            break;
          case 'notification':
            WebApp.HapticFeedback.notificationOccurred('success');
            break;
          case 'selection':
            WebApp.HapticFeedback.selectionChanged();
            break;
          default:
            WebApp.HapticFeedback.impactOccurred('medium');
        }
      }
    } catch (err) {
      console.error('触发触觉反馈失败:', err);
    }
  }, [isInitialized]);

  /**
   * 使用Telegram主题设置元素样式
   * @param {HTMLElement} element - 要设置样式的DOM元素
   * @param {Object} options - 样式选项
   */
  const applyThemeToElement = useCallback((element, options = {}) => {
    if (!isInitialized || !themeParams || !element) return;
    
    const {
      background = false,
      text = false,
      border = false,
      isButton = false,
    } = options;
    
    try {
      if (background) {
        element.style.backgroundColor = isButton 
          ? themeParams.button_color 
          : themeParams.bg_color;
      }
      
      if (text) {
        element.style.color = isButton 
          ? themeParams.button_text_color 
          : themeParams.text_color;
      }
      
      if (border) {
        element.style.borderColor = themeParams.hint_color;
      }
    } catch (err) {
      console.error('应用主题样式失败:', err);
    }
  }, [isInitialized, themeParams]);

  /**
   * 获取CSS变量对象，用于应用主题到整个应用
   * @returns {Object} CSS变量对象
   */
  const getThemeCssVars = useCallback(() => {
    if (!themeParams) return {};
    
    return {
      '--tg-theme-bg-color': themeParams.bg_color,
      '--tg-theme-text-color': themeParams.text_color,
      '--tg-theme-hint-color': themeParams.hint_color,
      '--tg-theme-link-color': themeParams.link_color,
      '--tg-theme-button-color': themeParams.button_color,
      '--tg-theme-button-text-color': themeParams.button_text_color,
      '--tg-theme-secondary-bg-color': themeParams.secondary_bg_color,
    };
  }, [themeParams]);

  return {
    isInitialized,
    isAvailable: !!WebApp.initData,
    userInfo,
    themeParams,
    error,
    platform: WebApp.platform,
    setMainButtonText,
    showMainButton,
    hideMainButton,
    setMainButtonClickHandler,
    triggerHapticFeedback,
    applyThemeToElement,
    getThemeCssVars,
    getColorScheme: () => WebApp.colorScheme,
  };
};

export default useTelegramSDK;