import { useState, useEffect } from 'react';
import useTelegramSDK from '../../hooks/useTelegramSDK';
import useSettingsStore from '../../store/settingsStore';

/**
 * 白名单管理组件
 * 提供白名单的显示、添加和删除功能
 */
const WhitelistManagement = ({ isOpen, onClose, onToast }) => {
  const [chatId, setChatId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const { isAvailable, themeParams } = useTelegramSDK();
  
  const { 
    whitelist, 
    loadWhitelist, 
    addToWhitelistAction, 
    removeFromWhitelistAction 
  } = useSettingsStore();

  // 组件挂载时加载白名单
  useEffect(() => {
    if (isOpen && !whitelist.isLoaded) {
      handleLoadWhitelist();
    }
  }, [isOpen]);

  // 加载白名单列表
  const handleLoadWhitelist = async () => {
    setIsLoadingList(true);
    try {
      await loadWhitelist();
    } catch (error) {
      console.error('加载白名单失败:', error);
      onToast && onToast('加载白名单失败', 'error');
    } finally {
      setIsLoadingList(false);
    }
  };

  // 添加到白名单
  const handleAdd = async () => {
    const id = parseInt(chatId.trim());
    if (!id || isNaN(id)) {
      onToast && onToast('请输入有效的聊天ID', 'error');
      return;
    }

    setIsLoading(true);
    try {
      await addToWhitelistAction(id);
      setChatId('');
      onToast && onToast('成功添加到白名单', 'success');
    } catch (error) {
      console.error('添加到白名单失败:', error);
      onToast && onToast('添加到白名单失败', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 从白名单移除
  const handleRemove = async (id) => {
    setIsLoading(true);
    try {
      await removeFromWhitelistAction(id);
      onToast && onToast('成功从白名单移除', 'success');
    } catch (error) {
      console.error('从白名单移除失败:', error);
      onToast && onToast('从白名单移除失败', 'error');
    } finally {
      setIsLoading(false);
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

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={overlayStyle}
      onClick={onClose}
    >
      <div 
        className="w-full max-w-md rounded-lg shadow-xl max-h-[80vh] overflow-hidden"
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">白名单管理</h2>
            <button
              onClick={onClose}
              className="p-1 rounded-md hover:bg-gray-100 transition-colors"
            >
              <span className="text-xl">×</span>
            </button>
          </div>
          <p className="text-sm opacity-70 mt-1">
            管理需要同步消息的聊天（用户/群组/频道）
          </p>
        </div>

        {/* 内容区域 */}
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {/* 添加新聊天 */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              添加聊天ID
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                placeholder="输入聊天ID（如：123456）"
                className="flex-1 px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                style={inputStyle}
                disabled={isLoading}
              />
              <button
                onClick={handleAdd}
                disabled={isLoading || !chatId.trim()}
                className="px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                style={buttonStyle}
              >
                {isLoading ? '添加中...' : '添加'}
              </button>
            </div>
          </div>

          {/* 白名单列表 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium">当前白名单</h3>
              <button
                onClick={handleLoadWhitelist}
                disabled={isLoadingList}
                className="text-xs px-2 py-1 rounded text-blue-600 hover:bg-blue-50 transition-colors"
              >
                {isLoadingList ? '刷新中...' : '刷新'}
              </button>
            </div>

            {isLoadingList ? (
              <div className="text-center py-4 text-sm opacity-70">
                加载中...
              </div>
            ) : whitelist.items.length === 0 ? (
              <div className="text-center py-4 text-sm opacity-70">
                暂无白名单项目
              </div>
            ) : (
              <div className="space-y-2">
                {whitelist.items.map((item) => (
                  <div 
                    key={item}
                    className="flex items-center justify-between p-3 rounded-md border"
                    style={{ borderColor: themeParams?.hint_color + '20' || '#e5e7eb' }}
                  >
                    <div>
                      <div className="text-sm font-medium">
                        聊天ID: {item}
                      </div>
                      <div className="text-xs opacity-70">
                        {item < 0 ? '群组/频道' : '用户'}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemove(item)}
                      disabled={isLoading}
                      className="px-3 py-1 rounded text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      style={dangerButtonStyle}
                    >
                      移除
                    </button>
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
};

export default WhitelistManagement;