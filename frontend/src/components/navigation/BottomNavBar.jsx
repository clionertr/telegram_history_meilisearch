import { useEffect } from 'react';
import useNavStore from '../../store/navStore';
import useTelegramSDK from '../../hooks/useTelegramSDK';

/**
 * 底部导航栏组件
 * 提供应用的主要导航功能：搜索、群组、设置
 */
function BottomNavBar() {
  const { activeNav, setActiveNav } = useNavStore();
  const { isAvailable, themeParams, triggerHapticFeedback } = useTelegramSDK();
  
  // 导航项配置
  const navItems = [
    { 
      id: 'search',
      icon: '🔍',
      label: '搜索',
    },
    { 
      id: 'groups',
      icon: '👥',
      label: '群组',
    },
    { 
      id: 'settings',
      icon: '⚙️',
      label: '设置',
    }
  ];
  
  // 处理导航项点击
  const handleNavClick = (navId) => {
    if (navId === activeNav) return;
    
    setActiveNav(navId);
    
    // 如果支持触觉反馈，则触发轻微的触觉反馈
    try {
      if (isAvailable) {
        triggerHapticFeedback('light');
      }
    } catch (error) {
      console.warn('触发触觉反馈失败，但继续执行:', error);
    }
  };
  
  // 获取导航项颜色样式
  const getNavItemStyles = (navId) => {
    const isActive = activeNav === navId;
    
    // 默认颜色
    let textColorClass = isActive ? 'text-blue-500' : 'text-gray-500';
    let customColor = {};
    
    // 如果在 Telegram 环境中，使用主题颜色
    if (isAvailable && themeParams) {
      if (isActive) {
        // 使用 Telegram 主题的按钮色或链接色
        customColor = {
          color: themeParams.button_color || themeParams.link_color
        };
      } else {
        // 使用 Telegram 主题的提示色
        customColor = {
          color: themeParams.hint_color
        };
      }
      textColorClass = ''; // 使用自定义颜色时清空默认类
    }
    
    return {
      className: `${textColorClass} flex flex-col items-center`,
      style: customColor
    };
  };
  
  // 导航栏样式
  const navBarStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color || '#ffffff',
    borderTop: `1px solid ${themeParams.hint_color}30` // 使用hint_color的30%透明度作为边框
  } : {
    backgroundColor: '#ffffff',
    borderTop: '1px solid rgba(0, 0, 0, 0.1)'
  };
  
  return (
    <nav 
      className="fixed bottom-0 left-0 right-0 flex justify-around py-2 shadow-lg" 
      style={navBarStyle}
    >
      {navItems.map(item => {
        const styles = getNavItemStyles(item.id);
        
        return (
          <button 
            key={item.id}
            onClick={() => handleNavClick(item.id)}
            className={styles.className}
            style={styles.style}
            aria-label={item.label}
            aria-current={activeNav === item.id ? 'page' : undefined}
          >
            <span className="text-xl mb-1">{item.icon}</span>
            <span className="text-xs">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

export default BottomNavBar;