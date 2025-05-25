import useTelegramSDK from '../hooks/useTelegramSDK';

/**
 * 搜索结果项组件 - 阶段3重构版本
 * 实现新的卡片式设计和现代化布局
 */
function ResultItem({ result }) {
  // 确保result存在
  if (!result) return null;

  // 使用TMA SDK钩子
  const { triggerHapticFeedback } = useTelegramSDK();

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
   * 将Unix时间戳转换为可读时间
   * @param {number} timestamp - Unix时间戳
   * @returns {string} 格式化的时间字符串
   */
  const formatTime = (timestamp) => {
    if (!timestamp) return '未知时间';
    
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    // 如果是今天，只显示时间
    if (messageDate.getTime() === today.getTime()) {
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    }
    
    // 如果是昨天
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (messageDate.getTime() === yesterday.getTime()) {
      return '昨天 ' + date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    }
    
    // 如果是今年，显示月日和时间
    if (date.getFullYear() === now.getFullYear()) {
      return date.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit'
      }) + ' ' + date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    }
    
    // 其他情况显示完整日期
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  /**
   * 处理消息链接点击
   */
  const handleLinkClick = () => {
    // 提供触觉反馈
    triggerHapticFeedback('selection');
  };

  /**
   * 处理卡片点击
   */
  const handleCardClick = () => {
    if (message_link) {
      triggerHapticFeedback('light');
      window.open(message_link, '_blank', 'noopener,noreferrer');
    }
  };

  // 生成消息ID用于标识（如果未提供ID）
  const messageId = id || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // 生成头像占位符
  const getAvatarPlaceholder = (name) => {
    if (!name) return '?';
    return name.charAt(0).toUpperCase();
  };

  // 处理消息内容，确保安全显示
  const getMessageContent = () => {
    if (!text_snippet) return '无消息内容';
    
    // 简单的HTML标签清理，保留高亮标签
    const cleanContent = text_snippet
      .replace(/<(?!\/?(em|strong)\b)[^>]*>/gi, '') // 移除除了em和strong之外的HTML标签
      .trim();
    
    return cleanContent || '无消息内容';
  };

  return (
    <div
      className="result-item"
      key={messageId}
      onClick={handleCardClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleCardClick();
        }
      }}
    >
      <div className="result-header">
        {/* 头像 */}
        <div className="result-avatar">
          {getAvatarPlaceholder(sender_name)}
        </div>
        
        {/* 发送者信息和时间 */}
        <div className="result-meta">
          <div className="result-sender">
            {sender_name || '未知发送者'}
          </div>
          <div className="result-time">
            {formatTime(date)}
          </div>
        </div>
      </div>

      {/* 消息内容 */}
      <div className="result-content">
        <div
          className="result-text"
          dangerouslySetInnerHTML={{
            __html: getMessageContent()
          }}
        />
        
        {/* 聊天标题 */}
        {chat_title && (
          <div className="result-chat">
            来自: {chat_title}
          </div>
        )}
      </div>

      {/* 链接指示器 */}
      {message_link && (
        <div className="result-link-indicator">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M7 17L17 7M17 7H7M17 7V17"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      )}
    </div>
  );
}

export default ResultItem;