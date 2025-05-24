import useTelegramSDK from '../hooks/useTelegramSDK';

/**
 * 搜索结果项组件
 * 显示单条搜索结果，包括消息摘要、发送者、聊天标题、发送时间及原始消息链接
 */
function ResultItem({ result }) {
  // 确保result存在
  if (!result) return null;

  // 使用TMA SDK钩子
  const { isAvailable, themeParams, triggerHapticFeedback } = useTelegramSDK();

  // 解构搜索结果数据
  const {
    id,
    chat_title,
    sender_name,
    text_snippet,
    date,
    message_link
  } = result;

  /**
   * 将Unix时间戳转换为可读日期
   * @param {number} timestamp - Unix时间戳
   * @returns {string} 格式化的日期字符串
   */
  const formatDate = (timestamp) => {
    if (!timestamp) return '未知时间';
    
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /**
   * 处理消息链接点击
   */
  const handleLinkClick = () => {
    // 提供触觉反馈
    triggerHapticFeedback('selection');
  };

  // 生成消息ID用于标识（如果未提供ID）
  const messageId = id || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Telegram主题样式
  const cardStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color,
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  } : {};

  const titleStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};

  const subtitleStyle = isAvailable && themeParams ? {
    color: themeParams.hint_color
  } : {};

  const contentStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};

  // 高亮样式
  const highlightStyles = `
    .result-content em {
      font-style: normal;
      font-weight: bold;
      ${isAvailable && themeParams
        ? `background-color: ${themeParams.accent_color || 'rgba(59, 130, 246, 0.2)'};
           color: ${themeParams.accent_text_color || themeParams.text_color};`
        : 'background-color: rgba(59, 130, 246, 0.2);'
      }
      padding: 0 2px;
      border-radius: 2px;
    }
  `;

  const linkStyle = isAvailable && themeParams ? {
    color: themeParams.link_color
  } : {};

  return (
    <div
      className="rounded-lg shadow-md p-4 mb-4 hover:shadow-lg transition-shadow"
      style={cardStyle}
      key={messageId}
    >
      {/* 高亮文本的样式 */}
      <style>{highlightStyles}</style>
      {/* 标题信息 */}
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold" style={titleStyle}>
            {chat_title || '未知聊天'}
          </h3>
          <p className="text-sm" style={subtitleStyle}>
            {sender_name || '未知发送者'} · {formatDate(date)}
          </p>
        </div>
      </div>

      {/* 消息内容 - 使用dangerouslySetInnerHTML渲染HTML标签 */}
      <p
        className="mb-3 whitespace-pre-line result-content"
        style={contentStyle}
        dangerouslySetInnerHTML={{
          __html: text_snippet || '无消息内容'
        }}
      />

      {/* 消息链接 */}
      {message_link && (
        <div className="text-right">
          <a
            href={message_link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium hover:opacity-80"
            style={linkStyle}
            onClick={handleLinkClick}
          >
            查看原始消息 →
          </a>
        </div>
      )}
    </div>
  );
}

export default ResultItem;