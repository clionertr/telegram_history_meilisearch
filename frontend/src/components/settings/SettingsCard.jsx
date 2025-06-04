import useTelegramSDK from '../../hooks/useTelegramSDK';

/**
 * 设置卡片组件
 * 用于在设置页面中展示一组相关的设置项
 * @param {Object} props
 * @param {string} props.title - 卡片标题（可选）
 * @param {React.ReactNode} props.children - 卡片内容（设置项）
 */
function SettingsCard({ title, children }) {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  // 卡片样式 - 优先使用Telegram主题，回退到我们的主题系统
  const cardStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color || undefined,
  } : {};
  
  // 卡片标题样式 - 优先使用Telegram主题
  const titleStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};
  
  return (
    <div 
      className="
        bg-bg-secondary 
        rounded-lg 
        overflow-hidden 
        mb-4 
        shadow-theme-sm
        border border-border-primary
        transition-theme
      " 
      style={cardStyle}
    >
      {/* 如果提供了标题，则渲染标题区域 */}
      {title && (
        <div className="px-4 py-3 border-b border-border-primary">
          <h3 
            className="text-base font-medium text-text-primary transition-theme" 
            style={titleStyle}
          >
            {title}
          </h3>
        </div>
      )}
      
      {/* 设置项容器 */}
      <div className="divide-y divide-border-primary">
        {children}
      </div>
    </div>
  );
}

export default SettingsCard;