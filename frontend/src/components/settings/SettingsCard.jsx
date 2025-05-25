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
  
  // 卡片样式
  const cardStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color || '#ffffff',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
  } : {
    backgroundColor: '#ffffff',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
  };
  
  // 卡片标题样式
  const titleStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};
  
  return (
    <div 
      className="rounded-lg overflow-hidden mb-4" 
      style={cardStyle}
    >
      {/* 如果提供了标题，则渲染标题区域 */}
      {title && (
        <div className="px-4 py-3 border-b border-gray-100">
          <h3 
            className="text-md font-medium" 
            style={titleStyle}
          >
            {title}
          </h3>
        </div>
      )}
      
      {/* 设置项容器 */}
      <div className="divide-y divide-gray-100">
        {children}
      </div>
    </div>
  );
}

export default SettingsCard;