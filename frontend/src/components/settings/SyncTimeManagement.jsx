import { useState, useEffect } from 'react';
import useTelegramSDK from '../../hooks/useTelegramSDK';
import useNavStore from '../../store/navStore';
import useSettingsStore from '../../store/settingsStore';
import SettingsCard from './SettingsCard';
import { SettingsNavigationItem, SettingsInfoItem } from './SettingsItems';

/**
 * 最旧同步时间管理组件
 * 允许用户设置全局和特定聊天的最旧同步时间戳
 */
function SyncTimeManagement({ isOpen, onClose, onToast }) {
  const { isAvailable, themeParams } = useTelegramSDK();
  const { hideBottomNav, showBottomNav } = useNavStore();
  
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

  // 控制底部导航栏的显示/隐藏
  useEffect(() => {
    if (isOpen) {
      hideBottomNav();
    } else {
      showBottomNav();
    }
    
    return () => {
      showBottomNav();
    };
  }, [isOpen, hideBottomNav, showBottomNav]);

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
  const overlayStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.bg_color
  } : {
    backgroundColor: '#f9fafb'
  };

  const titleStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};

  const inputStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color || '#ffffff',
    color: themeParams.text_color,
    borderColor: themeParams.hint_color + '50'
  } : {
    backgroundColor: '#ffffff',
    borderColor: '#d1d5db'
  };

  const buttonStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.button_color,
    color: themeParams.button_text_color
  } : {
    backgroundColor: '#3b82f6',
    color: '#ffffff'
  };

  const secondaryButtonStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color || '#f3f4f6',
    color: themeParams.text_color,
    borderColor: themeParams.hint_color + '50'
  } : {
    backgroundColor: '#f3f4f6',
    color: '#374151',
    borderColor: '#d1d5db'
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
      className="fixed inset-0 z-50 overflow-y-auto"
      style={overlayStyle}
    >
      {/* 头部 */}
      <header className="px-4 py-4 flex items-center justify-between border-b border-gray-200">
        <h1 className="text-xl font-medium" style={titleStyle}>
          最旧同步时间管理
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefreshData}
            className="px-3 py-1 text-sm rounded-lg border"
            style={secondaryButtonStyle}
            disabled={isLoading || isRefreshing}
          >
            {isRefreshing ? '刷新中...' : '🔄 刷新'}
          </button>
          <button
            onClick={onClose}
            className="text-2xl leading-none"
            style={titleStyle}
            disabled={isLoading}
          >
            ×
          </button>
        </div>
      </header>

      {/* 内容区域 */}
      <div className="px-4 py-4">
        {/* 说明文字 */}
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            设置最旧同步时间可以限制历史消息同步的范围。早于设定时间的消息将不会被同步。
            全局设置适用于所有聊天，特定聊天设置会覆盖全局设置。
          </p>
        </div>

        {/* 全局设置卡片 */}
        <SettingsCard title="全局设置">
          <SettingsInfoItem
            icon="🌍"
            label="全局最旧同步时间"
            value={formatTimestamp(oldestSyncSettings.global)}
          />
          
          <SettingsNavigationItem
            icon="⚙️"
            label="设置全局时间"
            description="为所有聊天设置统一的最旧同步时间"
            onNavigate={() => {
              // 如果有现有的全局时间戳，转换并填充到表单中
              if (oldestSyncSettings.global) {
                const dateTimeLocal = convertISOToDateTime(oldestSyncSettings.global);
                setGlobalDateTime(dateTimeLocal);
              }
              setShowGlobalForm(!showGlobalForm);
            }}
          />
          
          {oldestSyncSettings.global && (
            <SettingsNavigationItem
              icon="🗑️"
              label="移除全局设置"
              description="移除全局最旧同步时间限制"
              onNavigate={handleRemoveGlobalTimestamp}
            />
          )}
        </SettingsCard>

        {/* 全局设置表单 */}
        {showGlobalForm && (
          <SettingsCard title="设置全局时间">
            <div className="p-4">
              <label className="block text-sm font-medium mb-2" style={titleStyle}>
                选择最旧同步时间
              </label>
              <input
                type="datetime-local"
                value={globalDateTime}
                onChange={(e) => setGlobalDateTime(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm"
                style={inputStyle}
                disabled={isLoading}
              />
              <p className="text-xs text-gray-500 mt-1">
                选择的时间将作为全局最旧同步时间，早于此时间的消息将不会被同步
              </p>
              <div className="flex gap-2 mt-4">
                <button
                  onClick={handleSetGlobalTimestamp}
                  disabled={isLoading}
                  className="px-4 py-2 rounded-lg text-sm font-medium"
                  style={buttonStyle}
                >
                  {isLoading ? '设置中...' : '设置'}
                </button>
                <button
                  onClick={() => setShowGlobalForm(false)}
                  disabled={isLoading}
                  className="px-4 py-2 rounded-lg text-sm font-medium border"
                  style={secondaryButtonStyle}
                >
                  取消
                </button>
              </div>
            </div>
          </SettingsCard>
        )}

        {/* 特定聊天设置卡片 */}
        <SettingsCard title="特定聊天设置">
          <SettingsNavigationItem
            icon="➕"
            label="添加聊天设置"
            description="为特定聊天设置最旧同步时间"
            onNavigate={() => setShowChatForm(!showChatForm)}
          />
          
          {/* 显示现有的聊天设置 */}
          {Object.entries(oldestSyncSettings.chats || {}).map(([chatIdKey, timestamp]) => (
            <div key={chatIdKey} className="flex items-center justify-between p-3 border-b border-gray-100 last:border-b-0">
              <div>
                <div className="font-medium" style={titleStyle}>聊天 {chatIdKey}</div>
                <div className="text-sm opacity-70" style={titleStyle}>
                  {formatTimestamp(timestamp)}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleEditChatTimestamp(chatIdKey, timestamp)}
                  disabled={isLoading || isRefreshing}
                  className="text-blue-500 text-sm px-2 py-1 rounded"
                >
                  编辑
                </button>
                <button
                  onClick={() => handleRemoveChatTimestamp(chatIdKey)}
                  disabled={isLoading || isRefreshing}
                  className="text-red-500 text-sm px-2 py-1 rounded"
                >
                  移除
                </button>
              </div>
            </div>
          ))}
          
          {Object.keys(oldestSyncSettings.chats || {}).length === 0 && (
            <div className="p-4 text-center text-gray-500">
              暂无特定聊天设置
            </div>
          )}
        </SettingsCard>

        {/* 聊天设置表单 */}
        {showChatForm && (
          <SettingsCard title={editingChatId ? "编辑聊天设置" : "添加聊天设置"}>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={titleStyle}>
                  聊天ID
                </label>
                <input
                  type="text"
                  value={chatId}
                  onChange={(e) => setChatId(e.target.value)}
                  placeholder="-1001234567890"
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  style={inputStyle}
                  disabled={isLoading || editingChatId} // 编辑模式下禁用聊天ID输入
                />
                <p className="text-xs text-gray-500 mt-1">
                  {editingChatId ? '正在编辑聊天ID: ' + editingChatId : '输入要设置的聊天ID（数字格式）'}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={titleStyle}>
                  选择最旧同步时间
                </label>
                <input
                  type="datetime-local"
                  value={chatDateTime}
                  onChange={(e) => setChatDateTime(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  style={inputStyle}
                  disabled={isLoading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  此设置将覆盖该聊天的全局设置
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleSetChatTimestamp}
                  disabled={isLoading}
                  className="px-4 py-2 rounded-lg text-sm font-medium"
                  style={buttonStyle}
                >
                  {isLoading ? (editingChatId ? '修改中...' : '设置中...') : (editingChatId ? '修改' : '设置')}
                </button>
                <button
                  onClick={handleCancelEdit}
                  disabled={isLoading}
                  className="px-4 py-2 rounded-lg text-sm font-medium border"
                  style={secondaryButtonStyle}
                >
                  取消
                </button>
              </div>
            </div>
          </SettingsCard>
        )}
      </div>
    </div>
  );
}

export default SyncTimeManagement;
