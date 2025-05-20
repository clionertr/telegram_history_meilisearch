/**
 * 搜索结果项组件
 * 显示单条搜索结果，包括消息摘要、发送者、聊天标题、发送时间及原始消息链接
 */
function ResultItem({ result }) {
  // 确保result存在
  if (!result) return null;

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

  // 生成消息ID用于标识（如果未提供ID）
  const messageId = id || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-4 hover:shadow-lg transition-shadow"
      key={messageId}
    >
      {/* 标题信息 */}
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-gray-800 dark:text-gray-200">
            {chat_title || '未知聊天'}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {sender_name || '未知发送者'} · {formatDate(date)}
          </p>
        </div>
      </div>

      {/* 消息内容 */}
      <p className="text-gray-700 dark:text-gray-300 mb-3 whitespace-pre-line">
        {text_snippet || '无消息内容'}
      </p>

      {/* 消息链接 */}
      {message_link && (
        <div className="text-right">
          <a
            href={message_link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-medium"
          >
            查看原始消息 →
          </a>
        </div>
      )}
    </div>
  );
}

export default ResultItem;