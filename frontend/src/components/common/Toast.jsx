import { useState, useEffect } from 'react';
import useTelegramSDK from '../../hooks/useTelegramSDK';

/**
 * Toast 通知组件
 * 提供友好的消息提示，替代传统的 alert
 */
const Toast = ({ message, type = 'success', duration = 3000, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);
  const { isAvailable, themeParams } = useTelegramSDK();

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => {
        onClose && onClose();
      }, 300); // 等待动画完成
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  // 根据类型和主题确定样式
  const getToastStyle = () => {
    const baseStyle = {
      transition: 'all 0.3s ease-in-out',
      transform: isVisible ? 'translateY(0)' : 'translateY(-100%)',
      opacity: isVisible ? 1 : 0,
    };

    if (isAvailable && themeParams) {
      return {
        ...baseStyle,
        backgroundColor: type === 'success' 
          ? themeParams.button_color 
          : type === 'error' 
            ? '#dc2626' 
            : themeParams.secondary_bg_color,
        color: type === 'success' 
          ? themeParams.button_text_color 
          : '#ffffff',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      };
    }

    // 默认样式
    return {
      ...baseStyle,
      backgroundColor: type === 'success' 
        ? '#10b981' 
        : type === 'error' 
          ? '#dc2626' 
          : '#6b7280',
      color: '#ffffff',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    };
  };

  // 获取图标
  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'info':
        return 'ℹ';
      default:
        return '✓';
    }
  };

  return (
    <div 
      className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-4 py-3 rounded-lg flex items-center gap-2 min-w-48 max-w-80"
      style={getToastStyle()}
    >
      <span className="text-lg">{getIcon()}</span>
      <span className="text-sm font-medium flex-1">{message}</span>
    </div>
  );
};

/**
 * Toast 管理器组件
 * 管理多个 Toast 通知的显示
 */
export const ToastManager = ({ toasts, removeToast }) => {
  return (
    <div className="fixed top-0 left-0 right-0 z-50 pointer-events-none">
      {toasts.map((toast, index) => (
        <div 
          key={toast.id} 
          style={{ 
            marginTop: `${index * 60}px`,
            pointerEvents: 'auto'
          }}
        >
          <Toast
            message={toast.message}
            type={toast.type}
            duration={toast.duration}
            onClose={() => removeToast(toast.id)}
          />
        </div>
      ))}
    </div>
  );
};

export default Toast;