import useTelegramSDK from '../hooks/useTelegramSDK';

/**
 * 群组页面组件（占位）
 * 目前为占位页面，具体功能待定
 */
function GroupsPage() {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  // 页面样式
  const pageStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.bg_color
  } : {
    backgroundColor: '#f9fafb'
  };
  
  // 文本样式
  const textStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};
  
  // 描述文本样式
  const descStyle = isAvailable && themeParams ? {
    color: themeParams.hint_color
  } : {
    color: 'rgb(107 114 128)'
  };
  
  return (
    <div 
      className="w-full max-w-4xl mx-auto h-screen flex flex-col items-center justify-center px-4 pb-16" 
      style={pageStyle}
    >
      {/* 页面标题 */}
      <header className="text-center mb-4">
        <h1 className="text-2xl font-medium" style={textStyle}>群组</h1>
      </header>
      
      {/* 占位内容 */}
      <div className="text-center">
        <div className="text-5xl mb-4">👥</div>
        <p className="mb-2" style={textStyle}>群组功能即将推出</p>
        <p style={descStyle}>此功能正在开发中，敬请期待...</p>
      </div>
    </div>
  );
}

export default GroupsPage;