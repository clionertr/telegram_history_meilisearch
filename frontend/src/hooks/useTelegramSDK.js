/**
 * TMA SDK钩子 - 封装Telegram Mini App SDK功能
 */
import { useEffect, useState, useCallback } from 'react';

// 默认主题参数 - 在非TMA环境中使用
const defaultThemeParams = {
  bg_color: '#ffffff',
  text_color: '#000000',
  hint_color: '#999999',
  link_color: '#2481cc',
  button_color: '#2481cc',
  button_text_color: '#ffffff',
  secondary_bg_color: '#f0f0f0'
};

// 安全地获取WebApp对象
let WebApp = null;
try {
  // 首先尝试从window获取
  if (typeof window !== 'undefined' && window.Telegram && window.Telegram.WebApp) {
    WebApp = window.Telegram.WebApp;
    console.log('已从window.Telegram.WebApp获取到WebApp对象');
  } else {
    // 如果window中不存在，尝试导入
    try {
      // 动态导入可能会失败，但不会阻塞渲染
      import('@telegram-apps/sdk').then(module => {
        WebApp = module.default;
        console.log('已从@telegram-apps/sdk导入WebApp对象');
      }).catch(err => {
        console.warn('导入@telegram-apps/sdk失败:', err);
      });
    } catch (importErr) {
      console.warn('尝试导入SDK失败:', importErr);
    }
  }
} catch (e) {
  console.warn('初始化TMA SDK失败，将使用降级模式:', e);
}

/**
 * 检查SDK是否可用
 * @returns {boolean} SDK是否可用
 */
const isTMAAvailable = () => {
  try {
    return !!WebApp && (!!WebApp.initData || typeof WebApp.isExpanded !== 'undefined');
  } catch (e) {
    console.warn('检查TMA可用性失败:', e);
    return false;
  }
};

/**
 * 使用Telegram SDK的自定义钩子
 * 封装TMA SDK的核心功能，包括初始化、用户信息获取、主题颜色、MainButton管理等
 */
export const useTelegramSDK = () => {
  // 状态
  const [isInitialized, setIsInitialized] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [themeParams, setThemeParams] = useState(defaultThemeParams);
  const [error, setError] = useState(null);
  const [isAvailable, setIsAvailable] = useState(false);

  // 初始化TMA SDK
  useEffect(() => {
    // 检查SDK是否可用
    const checkAvailability = () => {
      const sdkAvailable = isTMAAvailable();
      setIsAvailable(sdkAvailable);
      return sdkAvailable;
    };
    
    if (!checkAvailability()) {
      console.log('Telegram Mini App SDK不可用，将使用默认设置');
      setIsInitialized(true);
      return;
    }
    
    try {
      // 初始化
      if (WebApp && typeof WebApp.ready === 'function') {
        WebApp.ready();
      }
      
      // 扩展视图（如果可能）
      try {
        if (WebApp && WebApp.isExpanded !== true && typeof WebApp.expand === 'function') {
          WebApp.expand();
        }
      } catch (expandErr) {
        console.warn('扩展视图失败，但将继续:', expandErr);
      }
      
      // 获取用户信息
      try {
        if (WebApp && WebApp.initDataUnsafe?.user) {
          setUserInfo({
            id: WebApp.initDataUnsafe.user.id,
            username: WebApp.initDataUnsafe.user.username || '',
            firstName: WebApp.initDataUnsafe.user.first_name || '',
            lastName: WebApp.initDataUnsafe.user.last_name || '',
            languageCode: WebApp.initDataUnsafe.user.language_code || 'zh',
          });
        }
      } catch (userErr) {
        console.warn('获取用户信息失败:', userErr);
      }
      
      // 获取主题参数 - 注意添加了全面的防御检查
      try {
        if (WebApp && WebApp.themeParams) {
          setThemeParams({
            bg_color: WebApp.themeParams.bg_color || defaultThemeParams.bg_color,
            text_color: WebApp.themeParams.text_color || defaultThemeParams.text_color,
            hint_color: WebApp.themeParams.hint_color || defaultThemeParams.hint_color,
            link_color: WebApp.themeParams.link_color || defaultThemeParams.link_color,
            button_color: WebApp.themeParams.button_color || defaultThemeParams.button_color,
            button_text_color: WebApp.themeParams.button_text_color || defaultThemeParams.button_text_color,
            secondary_bg_color: WebApp.themeParams.secondary_bg_color || defaultThemeParams.secondary_bg_color,
          });
        }
      } catch (themeErr) {
        console.warn('获取主题参数失败，使用默认主题:', themeErr);
      }
      
      setIsInitialized(true);
    } catch (err) {
      console.error('TMA SDK初始化失败:', err);
      setError(err.message || '初始化失败');
      // 即使初始化失败，也将isInitialized设为true，以避免UI阻塞
      setIsInitialized(true);
    }
  }, []);

  /**
   * 安全地访问WebApp对象的方法
   * @param {Function} fn - 要执行的函数
   * @param {*} defaultValue - 如果执行失败，返回的默认值
   * @returns {*} 函数执行结果或默认值
   */
  const safelyAccess = useCallback((fn, defaultValue = undefined) => {
    if (!isAvailable || !WebApp) return defaultValue;
    try {
      return fn();
    } catch (err) {
      console.warn('TMA SDK操作失败:', err);
      return defaultValue;
    }
  }, [isAvailable]);

  /**
   * 设置MainButton的文本
   * @param {string} text - 按钮文本
   */
  const setMainButtonText = useCallback((text) => {
    if (!isInitialized || !isAvailable || !WebApp) return;
    safelyAccess(() => {
      if (WebApp.MainButton && typeof WebApp.MainButton.setText === 'function') {
        WebApp.MainButton.setText(text);
      }
    });
  }, [isInitialized, isAvailable, safelyAccess]);

  /**
   * 显示MainButton
   * @param {string} [text] - 可选的按钮文本
   */
  const showMainButton = useCallback((text) => {
    if (!isInitialized || !isAvailable || !WebApp) return;
    safelyAccess(() => {
      if (WebApp.MainButton) {
        if (text && typeof WebApp.MainButton.setText === 'function') {
          WebApp.MainButton.setText(text);
        }
        if (typeof WebApp.MainButton.show === 'function') {
          WebApp.MainButton.show();
        }
      }
    });
  }, [isInitialized, isAvailable, safelyAccess]);

  /**
   * 隐藏MainButton
   */
  const hideMainButton = useCallback(() => {
    if (!isInitialized || !isAvailable || !WebApp) return;
    safelyAccess(() => {
      if (WebApp.MainButton && typeof WebApp.MainButton.hide === 'function') {
        WebApp.MainButton.hide();
      }
    });
  }, [isInitialized, isAvailable, safelyAccess]);

  /**
   * 设置MainButton点击事件
   * @param {Function} callback - 点击回调函数
   * @returns {Function} 清理函数，用于移除事件监听器
   */
  const setMainButtonClickHandler = useCallback((callback) => {
    if (!isInitialized || !isAvailable || !callback || !WebApp) return () => {};
    
    return safelyAccess(() => {
      if (WebApp.MainButton) {
        if (typeof WebApp.MainButton.onClick === 'function') {
          WebApp.MainButton.onClick(callback);
          
          // 返回清理函数
          return () => {
            if (typeof WebApp.MainButton.offClick === 'function') {
              WebApp.MainButton.offClick(callback);
            }
          };
        }
      }
      return () => {}; // 默认空清理函数
    }, () => {});
  }, [isInitialized, isAvailable, safelyAccess]);

  /**
   * 触发触觉反馈（如果支持）
   * @param {string} style - 反馈类型：'impact', 'notification', 'selection'
   */
  const triggerHapticFeedback = useCallback((style = 'impact') => {
    if (!isInitialized || !isAvailable || !WebApp) return;
    
    safelyAccess(() => {
      // 检查是否支持触觉反馈
      if (WebApp.HapticFeedback) {
        switch (style) {
          case 'impact':
            if (typeof WebApp.HapticFeedback.impactOccurred === 'function') {
              WebApp.HapticFeedback.impactOccurred('medium');
            }
            break;
          case 'notification':
            if (typeof WebApp.HapticFeedback.notificationOccurred === 'function') {
              WebApp.HapticFeedback.notificationOccurred('success');
            }
            break;
          case 'selection':
            if (typeof WebApp.HapticFeedback.selectionChanged === 'function') {
              WebApp.HapticFeedback.selectionChanged();
            }
            break;
          default:
            if (typeof WebApp.HapticFeedback.impactOccurred === 'function') {
              WebApp.HapticFeedback.impactOccurred('medium');
            }
        }
      }
    });
  }, [isInitialized, isAvailable, safelyAccess]);

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
      console.warn('应用样式失败:', err);
    }
  }, [isInitialized, themeParams]);

  /**
   * 获取CSS变量对象，用于应用主题到整个应用
   * @returns {Object} CSS变量对象
   */
  const getThemeCssVars = useCallback(() => {
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

  /**
   * 获取颜色方案（light或dark）
   * @returns {string} 颜色方案
   */
  const getColorScheme = useCallback(() => {
    return safelyAccess(() => WebApp.colorScheme, 'light');
  }, [safelyAccess]);

  return {
    isInitialized,
    isAvailable,
    userInfo,
    themeParams,
    error,
    platform: safelyAccess(() => WebApp.platform, 'unknown'),
    setMainButtonText,
    showMainButton,
    hideMainButton,
    setMainButtonClickHandler,
    triggerHapticFeedback,
    applyThemeToElement,
    getThemeCssVars,
    getColorScheme
  };
};

export default useTelegramSDK;