import { useState, useEffect } from 'react';
import useTelegramSDK from '../../hooks/useTelegramSDK';
import useSettingsStore from '../../store/settingsStore';

/**
 * 最旧同步时间管理组件
 * 允许用户设置全局和特定聊天的最旧同步时间戳
 */
function SyncTimeManagement({ isOpen, onClose, onToast }) {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  // 本地状态
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [globalDateTime, setGlobalDateTime] = useState('');
  const [chatDateTime, setChatDateTime] = useState('');
  const [chatId, setChatId] = useState('');
  const [showGlobalForm, setShowGlobalForm] = useState(false);
  const [showChatForm, setShowChatForm] = useState(false);
  const [editingChatId, setEditingChatId] = useState(null);
  
  // 从设置store获取状态和方法
  const {
    sync: { oldestSyncSettings },
    loadSyncSettings,
    setGlobalOldestSyncTimestamp,
    setChatOldestSyncTimestamp
  } = useSettingsStore();

  // 加载同步设置 - 每次打开时都强制刷新数据
  useEffect(() => {
    if (isOpen) {
      // 强制重新加载最新的同步设置数据
      loadSyncSettings();
    }
  }, [isOpen, loadSyncSettings]);

  // 手动刷新同步设置数据
  const handleRefreshData = async () => {
    setIsRefreshing(true);
    try {
      const result = await loadSyncSettings(true);
      if (result.success) {
        onToast && onToast('数据已刷新', 'success');
      } else {
        onToast && onToast('刷新失败: ' + result.error, 'error');
      }
    } catch (error) {
      onToast && onToast('刷新失败: ' + error.message, 'error');
    } finally {
      setIsRefreshing(false);
    }
  };

  // 日期时间转换辅助函数
  const convertDateTimeToISO = (dateTimeLocal) => {
    if (!dateTimeLocal) return '';
    try {
      // datetime-local 格式: YYYY-MM-DDTHH:mm
      // 转换为 ISO 8601 格式: YYYY-MM-DDTHH:mm:ss.sssZ
      const date = new Date(dateTimeLocal);
      return date.toISOString();
    } catch (error) {
      console.error('日期时间转换失败:', error);
      return '';
    }
  };

  const convertISOToDateTime = (isoString) => {
    if (!isoString) return '';
    try {
      // ISO 8601 格式转换为 datetime-local 格式
      const date = new Date(isoString);
      // 获取本地时间并格式化为 YYYY-MM-DDTHH:mm
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    } catch (error) {
      console.error('ISO时间转换失败:', error);
      return '';
    }
  };

  // 样式定义
  const overlayStyle = {
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    backdropFilter: 'blur(4px)',
  };

  const modalStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.bg_color,
    color: themeParams.text_color,
  } : {
    backgroundColor: '#ffffff',
    color: '#000000',
  };

  const inputStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color,
    borderColor: themeParams.hint_color + '40',
    color: themeParams.text_color,
  } : {
    backgroundColor: '#f9fafb',
    borderColor: '#d1d5db',
    color: '#111827',
  };

  const buttonStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.button_color,
    color: themeParams.button_text_color,
  } : {
    backgroundColor: '#3b82f6',
    color: '#ffffff',
  };

  const dangerButtonStyle = {
    backgroundColor: '#dc2626',
    color: '#ffffff',
  };

  // 格式化时间戳显示
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '未设置';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return '格式错误';
    }
  };

  // 处理设置全局时间戳
  const handleSetGlobalTimestamp = async () => {
    if (!globalDateTime.trim()) {
      onToast && onToast('请选择有效的日期时间', 'error');
      return;
    }

    const isoTimestamp = convertDateTimeToISO(globalDateTime);
    if (!isoTimestamp) {
      onToast && onToast('日期时间格式转换失败', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const result = await setGlobalOldestSyncTimestamp(isoTimestamp);
      if (result.success) {
        onToast && onToast('全局最旧同步时间设置成功', 'success');
        setGlobalDateTime('');
        setShowGlobalForm(false);
      } else {
        onToast && onToast(result.message || '设置失败', 'error');
      }
    } catch (error) {
      onToast && onToast('设置失败: ' + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 处理移除全局时间戳
  const handleRemoveGlobalTimestamp = async () => {
    setIsLoading(true);
    try {
      const result = await setGlobalOldestSyncTimestamp(null);
      if (result.success) {
        onToast && onToast('全局最旧同步时间已移除', 'success');
      } else {
        onToast && onToast(result.message || '移除失败', 'error');
      }
    } catch (error) {
      onToast && onToast('移除失败: ' + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 处理设置聊天时间戳
  const handleSetChatTimestamp = async () => {
    if (!chatId.trim() || !chatDateTime.trim()) {
      onToast && onToast('请输入有效的聊天ID和选择日期时间', 'error');
      return;
    }

    const chatIdNum = parseInt(chatId);
    if (isNaN(chatIdNum)) {
      onToast && onToast('聊天ID必须是数字', 'error');
      return;
    }

    const isoTimestamp = convertDateTimeToISO(chatDateTime);
    if (!isoTimestamp) {
      onToast && onToast('日期时间格式转换失败', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const result = await setChatOldestSyncTimestamp(chatIdNum, isoTimestamp);
      if (result.success) {
        const actionText = editingChatId ? '修改' : '设置';
        onToast && onToast(`聊天最旧同步时间${actionText}成功`, 'success');
        handleCancelEdit(); // 清理编辑状态
      } else {
        onToast && onToast(result.message || '设置失败', 'error');
      }
    } catch (error) {
      onToast && onToast('设置失败: ' + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 处理移除聊天时间戳
  const handleRemoveChatTimestamp = async (chatIdToRemove) => {
    setIsLoading(true);
    try {
      const result = await setChatOldestSyncTimestamp(parseInt(chatIdToRemove), null);
      if (result.success) {
        onToast && onToast('聊天最旧同步时间已移除', 'success');
      } else {
        onToast && onToast(result.message || '移除失败', 'error');
      }
    } catch (error) {
      onToast && onToast('移除失败: ' + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 处理编辑聊天时间戳
  const handleEditChatTimestamp = (chatIdKey, currentTimestamp) => {
    setEditingChatId(chatIdKey);
    setChatId(chatIdKey);
    // 将现有时间戳转换为datetime-local格式并填充
    const dateTimeLocal = convertISOToDateTime(currentTimestamp);
    setChatDateTime(dateTimeLocal);
    setShowChatForm(true);
  };

  // 处理取消编辑
  const handleCancelEdit = () => {
    setEditingChatId(null);
    setChatId('');
    setChatDateTime('');
    setShowChatForm(false);
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={overlayStyle}
      onClick={onClose}
    >
      <div 
        className="w-full max-w-2xl rounded-lg shadow-xl max-h-[90vh] overflow-hidden"
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">最旧同步时间管理</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRefreshData}
                disabled={isLoading || isRefreshing}
                className="px-3 py-1 text-sm rounded-lg border hover:bg-gray-100 transition-colors"
              >
                {isRefreshing ? '刷新中...' : '🔄'}
              </button>
              <button
                onClick={onClose}
                className="p-1 rounded-md hover:bg-gray-100 transition-colors"
              >
                <span className="text-xl">×</span>
              </button>
            </div>
          </div>
          <p className="text-sm opacity-70 mt-1">
            设置最旧同步时间可以限制历史消息同步的范围
          </p>
        </div>

        {/* 内容区域 */}
        <div className="px-6 py-4 max-h-[75vh] overflow-y-auto">
          {/* 全局设置 */}
          <div className="mb-6">
            <h3 className="text-md font-medium mb-3">全局设置</h3>
            <div className="p-4 border rounded-lg">
              <div className="mb-3">
                <span className="text-sm font-medium">当前全局时间: </span>
                <span className="text-sm">{formatTimestamp(oldestSyncSettings.global)}</span>
              </div>
              
              {!showGlobalForm ? (
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      if (oldestSyncSettings.global) {
                        const dateTimeLocal = convertISOToDateTime(oldestSyncSettings.global);
                        setGlobalDateTime(dateTimeLocal);
                      }
                      setShowGlobalForm(true);
                    }}
                    className="px-4 py-2 rounded-md text-sm font-medium"
                    style={buttonStyle}
                  >
                    {oldestSyncSettings.global ? '修改' : '设置'}全局时间
                  </button>
                  {oldestSyncSettings.global && (
                    <button
                      onClick={handleRemoveGlobalTimestamp}
                      disabled={isLoading}
                      className="px-4 py-2 rounded-md text-sm font-medium"
                      style={dangerButtonStyle}
                    >
                      移除全局设置
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <input
                    type="datetime-local"
                    value={globalDateTime}
                    onChange={(e) => setGlobalDateTime(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md text-sm"
                    style={inputStyle}
                    disabled={isLoading}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleSetGlobalTimestamp}
                      disabled={isLoading}
                      className="px-4 py-2 rounded-md text-sm font-medium"
                      style={buttonStyle}
                    >
                      {isLoading ? '设置中...' : '确认'}
                    </button>
                    <button
                      onClick={() => setShowGlobalForm(false)}
                      disabled={isLoading}
                      className="px-4 py-2 rounded-md text-sm font-medium border"
                    >
                      取消
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 特定聊天设置 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-md font-medium">特定聊天设置</h3>
              <button
                onClick={() => setShowChatForm(!showChatForm)}
                className="text-sm px-3 py-1 rounded text-blue-600 hover:bg-blue-50 transition-colors"
              >
                {showChatForm ? '取消添加' : '+ 添加聊天'}
              </button>
            </div>

            {/* 添加/编辑聊天表单 */}
            {showChatForm && (
              <div className="mb-4 p-4 border rounded-lg bg-gray-50">
                <h4 className="text-sm font-medium mb-3">
                  {editingChatId ? `编辑聊天 ${editingChatId}` : '添加新聊天设置'}
                </h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium mb-1">聊天ID</label>
                    <input
                      type="text"
                      value={chatId}
                      onChange={(e) => setChatId(e.target.value)}
                      placeholder="-1001234567890"
                      className="w-full px-3 py-2 border rounded-md text-sm"
                      style={inputStyle}
                      disabled={isLoading || editingChatId}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">最旧同步时间</label>
                    <input
                      type="datetime-local"
                      value={chatDateTime}
                      onChange={(e) => setChatDateTime(e.target.value)}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                      style={inputStyle}
                      disabled={isLoading}
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleSetChatTimestamp}
                      disabled={isLoading}
                      className="px-4 py-2 rounded-md text-sm font-medium"
                      style={buttonStyle}
                    >
                      {isLoading ? (editingChatId ? '修改中...' : '设置中...') : (editingChatId ? '修改' : '设置')}
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      disabled={isLoading}
                      className="px-4 py-2 rounded-md text-sm font-medium border"
                    >
                      取消
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 现有聊天设置列表 */}
            {Object.keys(oldestSyncSettings.chats || {}).length === 0 ? (
              <div className="text-center py-4 text-sm opacity-70">
                暂无特定聊天设置
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(oldestSyncSettings.chats || {}).map(([chatIdKey, timestamp]) => (
                  <div 
                    key={chatIdKey}
                    className="flex items-center justify-between p-3 rounded-md border"
                  >
                    <div>
                      <div className="text-sm font-medium">
                        聊天 {chatIdKey}
                      </div>
                      <div className="text-xs opacity-70">
                        {formatTimestamp(timestamp)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleEditChatTimestamp(chatIdKey, timestamp)}
                        disabled={isLoading || isRefreshing}
                        className="text-blue-500 text-sm px-2 py-1 rounded hover:bg-blue-50"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleRemoveChatTimestamp(chatIdKey)}
                        disabled={isLoading || isRefreshing}
                        className="text-red-500 text-sm px-2 py-1 rounded hover:bg-red-50"
                      >
                        移除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 底部 */}
        <div className="px-6 py-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 rounded-md text-sm font-medium bg-gray-500 text-white hover:bg-gray-600 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}

export default SyncTimeManagement;
