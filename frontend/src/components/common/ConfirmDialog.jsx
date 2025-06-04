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
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div 
        className="w-full max-w-sm rounded-lg shadow-theme-xl overflow-hidden bg-bg-primary border border-border-primary transition-theme"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="px-6 py-4 text-center">
          <div className="text-3xl mb-3">
            {getIcon()}
          </div>
          <h3 className="text-lg font-semibold mb-2 text-text-primary transition-theme">
            {title}
          </h3>
          <p className="text-sm text-text-secondary leading-relaxed transition-theme">
            {message}
          </p>
        </div>

        {/* 底部按钮 */}
        <div className="px-6 py-4 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-md text-sm font-medium transition-theme bg-bg-secondary text-text-primary border border-border-primary hover:bg-bg-tertiary"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-theme ${
              type === 'danger' 
                ? 'bg-error text-white hover:bg-error/90' 
                : type === 'warning'
                ? 'bg-warning text-white hover:bg-warning/90'
                : 'bg-accent-primary text-white hover:bg-accent-hover'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;