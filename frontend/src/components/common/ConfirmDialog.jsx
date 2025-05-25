import useTelegramSDK from '../../hooks/useTelegramSDK';

/**
 * 确认对话框组件
 * 提供二次确认功能
 */
const ConfirmDialog = ({ 
  isOpen, 
  title, 
  message, 
  confirmText = '确认', 
  cancelText = '取消', 
  onConfirm, 
  onCancel,
  type = 'warning' // 'warning', 'danger', 'info'
}) => {
  const { isAvailable, themeParams } = useTelegramSDK();

  // 样式定义
  const overlayStyle = {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    backdropFilter: 'blur(4px)',
  };

  const modalStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.bg_color,
    color: themeParams.text_color,
  } : {
    backgroundColor: '#ffffff',
    color: '#000000',
  };

  const confirmButtonStyle = () => {
    const baseStyle = {
      fontWeight: '500',
      transition: 'all 0.2s ease',
    };

    if (type === 'danger') {
      return {
        ...baseStyle,
        backgroundColor: '#dc2626',
        color: '#ffffff',
      };
    } else if (type === 'warning') {
      return {
        ...baseStyle,
        backgroundColor: '#f59e0b',
        color: '#ffffff',
      };
    } else {
      return isAvailable && themeParams ? {
        ...baseStyle,
        backgroundColor: themeParams.button_color,
        color: themeParams.button_text_color,
      } : {
        ...baseStyle,
        backgroundColor: '#3b82f6',
        color: '#ffffff',
      };
    }
  };

  const cancelButtonStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color,
    color: themeParams.text_color,
    border: `1px solid ${themeParams.hint_color}40`,
  } : {
    backgroundColor: '#f9fafb',
    color: '#374151',
    border: '1px solid #d1d5db',
  };

  // 获取图标
  const getIcon = () => {
    switch (type) {
      case 'danger':
        return '⚠️';
      case 'warning':
        return '❓';
      case 'info':
        return 'ℹ️';
      default:
        return '❓';
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[60] flex items-center justify-center p-4"
      style={overlayStyle}
      onClick={onCancel}
    >
      <div 
        className="w-full max-w-sm rounded-lg shadow-xl overflow-hidden"
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="px-6 py-4 text-center">
          <div className="text-3xl mb-3">
            {getIcon()}
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {title}
          </h3>
          <p className="text-sm opacity-80 leading-relaxed">
            {message}
          </p>
        </div>

        {/* 底部按钮 */}
        <div className="px-6 py-4 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors hover:opacity-80"
            style={cancelButtonStyle}
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors hover:opacity-90"
            style={confirmButtonStyle()}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;