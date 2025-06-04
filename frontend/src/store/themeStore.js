import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

/**
 * 主题管理Store
 * 负责管理应用的主题状态、持久化和系统主题检测
 */
const useThemeStore = create(
  subscribeWithSelector((set, get) => ({
    // 当前主题: 'light' | 'dark' | 'system'
    theme: 'system',
    
    // 解析后的实际主题: 'light' | 'dark'
    resolvedTheme: 'light',
    
    // 是否正在初始化
    isInitializing: true,

    /**
     * 检测系统主题偏好
     */
    getSystemTheme: () => {
      if (typeof window === 'undefined') return 'light';
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },

    /**
     * 解析主题值
     * @param {string} theme - 主题值 ('light' | 'dark' | 'system')
     * @returns {string} 解析后的主题 ('light' | 'dark')
     */
    resolveTheme: (theme) => {
      if (theme === 'system') {
        return get().getSystemTheme();
      }
      return theme;
    },

    /**
     * 设置主题
     * @param {string} newTheme - 新主题 ('light' | 'dark' | 'system')
     */
    setTheme: (newTheme) => {
      const resolvedTheme = get().resolveTheme(newTheme);
      
      set({ 
        theme: newTheme, 
        resolvedTheme 
      });
      
      // 保存到localStorage
      try {
        localStorage.setItem('app-theme', newTheme);
      } catch (error) {
        console.warn('无法保存主题到localStorage:', error);
      }
      
      // 应用主题到HTML元素
      get().applyTheme(resolvedTheme);
    },

    /**
     * 切换主题 (在light和dark之间切换)
     */
    toggleTheme: () => {
      const { theme, resolvedTheme } = get();
      
      // 如果当前是system模式，则根据当前解析的主题切换到对应的固定主题
      if (theme === 'system') {
        get().setTheme(resolvedTheme === 'light' ? 'dark' : 'light');
      } else {
        // 在light和dark之间切换
        get().setTheme(theme === 'light' ? 'dark' : 'light');
      }
    },

    /**
     * 应用主题到HTML元素
     * @param {string} theme - 主题 ('light' | 'dark')
     */
    applyTheme: (theme) => {
      const root = document.documentElement;
      
      // 移除之前的主题类
      root.classList.remove('light', 'dark');
      
      // 添加新主题类
      root.classList.add(theme);
      
      // 设置CSS变量 (用于不支持Tailwind的样式)
      root.style.setProperty('--theme', theme);
      
      // 更新meta标签中的颜色方案
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', theme === 'dark' ? '#1f2937' : '#ffffff');
      }
    },

    /**
     * 初始化主题
     * 从localStorage读取保存的主题偏好，或使用系统主题
     */
    initializeTheme: () => {
      let savedTheme = 'system';
      
      // 尝试从localStorage读取保存的主题
      try {
        const stored = localStorage.getItem('app-theme');
        if (stored && ['light', 'dark', 'system'].includes(stored)) {
          savedTheme = stored;
        }
      } catch (error) {
        console.warn('无法从localStorage读取主题:', error);
      }
      
      const resolvedTheme = get().resolveTheme(savedTheme);
      
      set({ 
        theme: savedTheme, 
        resolvedTheme,
        isInitializing: false
      });
      
      // 应用主题
      get().applyTheme(resolvedTheme);
    },

    /**
     * 监听系统主题变化
     */
    setupSystemThemeListener: () => {
      if (typeof window === 'undefined') return;
      
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const handleChange = () => {
        const { theme } = get();
        // 只有在system模式下才响应系统主题变化
        if (theme === 'system') {
          const newResolvedTheme = get().getSystemTheme();
          set({ resolvedTheme: newResolvedTheme });
          get().applyTheme(newResolvedTheme);
        }
      };
      
      // 添加监听器
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleChange);
      } else {
        // 兼容旧版浏览器
        mediaQuery.addListener(handleChange);
      }
      
      // 返回清理函数
      return () => {
        if (mediaQuery.removeEventListener) {
          mediaQuery.removeEventListener('change', handleChange);
        } else {
          mediaQuery.removeListener(handleChange);
        }
      };
    },

    /**
     * 获取主题显示名称
     * @param {string} theme - 主题值
     * @returns {string} 显示名称
     */
    getThemeDisplayName: (theme) => {
      const names = {
        light: '浅色模式',
        dark: '深色模式',
        system: '跟随系统'
      };
      return names[theme] || theme;
    },

    /**
     * 获取当前主题的图标
     * @param {string} theme - 主题值
     * @returns {string} 图标名称或emoji
     */
    getThemeIcon: (theme) => {
      const icons = {
        light: '☀️',
        dark: '🌙',
        system: '💻'
      };
      return icons[theme] || '🎨';
    }
  }))
);

export default useThemeStore; 