import { useState, useEffect } from 'react';
import useTelegramSDK from '../../hooks/useTelegramSDK';
import useSettingsStore from '../../store/settingsStore';

/**
 * 白名单管理组件
 * 用于管理同步白名单
 */
const WhitelistManagement = ({ isOpen, onClose, onToast }) => {
  const { isAvailable, themeParams } = useTelegramSDK();
  const { 
    whitelist, 
    loadWhitelist, 
    addToWhitelistAction, 
    removeFromWhitelistAction 
  } = useSettingsStore();

  const [chatId, setChatId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingList, setIsLoadingList] = useState(false);

  // 初始加载白名单
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

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-md rounded-lg shadow-theme-xl max-h-[80vh] overflow-hidden bg-bg-primary border border-border-primary transition-theme"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="px-6 py-4 border-b border-border-primary">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text-primary transition-theme">白名单管理</h2>
            <button
              onClick={onClose}
              className="p-1 rounded-md hover:bg-bg-tertiary transition-theme text-text-secondary"
            >
              <span className="text-xl">×</span>
            </button>
          </div>
          <p className="text-sm text-text-secondary mt-1 transition-theme">
            管理需要同步消息的聊天（用户/群组/频道）
          </p>
        </div>

        {/* 内容区域 */}
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {/* 添加新聊天 */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2 text-text-primary transition-theme">
              添加聊天ID
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                placeholder="输入聊天ID（如：123456）"
                className="flex-1 px-3 py-2 border border-border-primary rounded-md text-sm bg-bg-secondary text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition-theme"
                disabled={isLoading}
              />
              <button
                onClick={handleAdd}
                disabled={isLoading || !chatId.trim()}
                className="px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-theme bg-accent-primary text-white hover:bg-accent-hover"
              >
                {isLoading ? '添加中...' : '添加'}
              </button>
            </div>
          </div>

          {/* 白名单列表 */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-text-primary transition-theme">当前白名单</h3>
              <button
                onClick={handleLoadWhitelist}
                disabled={isLoadingList}
                className="text-xs px-2 py-1 rounded text-accent-primary hover:bg-accent-primary/10 transition-theme"
              >
                {isLoadingList ? '刷新中...' : '刷新'}
              </button>
            </div>

            {isLoadingList ? (
              <div className="text-center py-4 text-sm text-text-secondary transition-theme">
                加载中...
              </div>
            ) : whitelist.items.length === 0 ? (
              <div className="text-center py-4 text-sm text-text-secondary transition-theme">
                暂无白名单项目
              </div>
            ) : (
              <div className="space-y-2">
                {whitelist.items.map((item) => (
                  <div 
                    key={item}
                    className="flex items-center justify-between p-3 rounded-md border border-border-secondary bg-bg-secondary transition-theme"
                  >
                    <div>
                      <div className="text-sm font-medium text-text-primary transition-theme">
                        聊天ID: {item}
                      </div>
                      <div className="text-xs text-text-secondary transition-theme">
                        {item < 0 ? '群组/频道' : '用户'}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemove(item)}
                      disabled={isLoading}
                      className="px-3 py-1 rounded text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-theme bg-error text-white hover:bg-error/80"
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
        <div className="px-6 py-4 border-t border-border-primary">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 rounded-md text-sm font-medium bg-bg-secondary text-text-primary border border-border-primary hover:bg-bg-tertiary transition-theme"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default WhitelistManagement;