import { useState, useEffect } from 'react';
import useTelegramSDK from '../../hooks/useTelegramSDK';
import useNavStore from '../../store/navStore';
import { getCacheTypes, clearCacheTypes, clearAllCache } from '../../services/api';
import ConfirmDialog from '../common/ConfirmDialog';

/**
 * 缓存管理组件
 * 提供多种缓存清除选项的界面
 */
const CacheManagement = ({ isOpen, onClose, onToast }) => {
  const [cacheTypes, setCacheTypes] = useState({});
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingTypes, setIsLoadingTypes] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({
    isOpen: false,
    title: '',
    message: '',
    action: null
  });
  
  const { isAvailable, themeParams } = useTelegramSDK();
  const { hideBottomNav, showBottomNav } = useNavStore();

  // 组件挂载时加载缓存类型
  useEffect(() => {
    if (isOpen) {
      loadCacheTypes();
    }
  }, [isOpen]);

  // 控制底部导航栏的显示/隐藏
  useEffect(() => {
    if (isOpen) {
      hideBottomNav(); // 缓存管理界面打开时隐藏底部栏
    } else {
      showBottomNav(); // 缓存管理界面关闭时恢复底部栏
    }
    
    // 清理函数：组件卸载时确保恢复底部栏
    return () => {
      showBottomNav();
    };
  }, [isOpen, hideBottomNav, showBottomNav]);

  // 加载缓存类型
  const loadCacheTypes = async () => {
    setIsLoadingTypes(true);
    try {
      const response = await getCacheTypes();
      setCacheTypes(response.cache_types || {});
    } catch (error) {
      console.error('加载缓存类型失败:', error);
      onToast && onToast('加载缓存类型失败', 'error');
    } finally {
      setIsLoadingTypes(false);
    }
  };

  // 切换缓存类型选择
  const toggleCacheType = (type) => {
    setSelectedTypes(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type);
      } else {
        return [...prev, type];
      }
    });
  };

  // 全选/全不选
  const toggleSelectAll = () => {
    const allTypes = Object.keys(cacheTypes);
    if (selectedTypes.length === allTypes.length) {
      setSelectedTypes([]);
    } else {
      setSelectedTypes(allTypes);
    }
  };

  // 显示清除选中缓存的确认对话框
  const showClearSelectedConfirm = () => {
    if (selectedTypes.length === 0) {
      onToast && onToast('请选择要清除的缓存类型', 'error');
      return;
    }

    const selectedNames = selectedTypes.map(type => cacheTypes[type]?.name).join('、');
    setConfirmDialog({
      isOpen: true,
      title: '确认清除缓存',
      message: `您确定要清除以下缓存吗？\n\n${selectedNames}\n\n此操作不可撤销。`,
      action: 'clearSelected'
    });
  };

  // 显示清除所有缓存的确认对话框
  const showClearAllConfirm = () => {
    setConfirmDialog({
      isOpen: true,
      title: '确认清除所有缓存',
      message: '您确定要清除所有缓存吗？\n\n这将删除所有搜索数据和应用状态，此操作不可撤销。',
      action: 'clearAll'
    });
  };

  // 处理确认对话框的确认操作
  const handleConfirmAction = async () => {
    const { action } = confirmDialog;
    setConfirmDialog({ isOpen: false, title: '', message: '', action: null });

    if (action === 'clearSelected') {
      await executeClearSelected();
    } else if (action === 'clearAll') {
      await executeClearAll();
    }
  };

  // 处理确认对话框的取消操作
  const handleCancelAction = () => {
    setConfirmDialog({ isOpen: false, title: '', message: '', action: null });
  };

  // 执行清除选中的缓存
  const executeClearSelected = async () => {
    setIsLoading(true);
    try {
      const response = await clearCacheTypes(selectedTypes);
      
      if (response.success) {
        onToast && onToast(response.message, 'success');
        setSelectedTypes([]);
        
        // 如果包含前端状态缓存，执行本地清除
        if (selectedTypes.includes('frontend_state')) {
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        }
      } else {
        onToast && onToast(response.message, 'error');
      }
    } catch (error) {
      console.error('清除缓存失败:', error);
      onToast && onToast('清除缓存失败', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // 执行清除所有缓存
  const executeClearAll = async () => {
    setIsLoading(true);
    try {
      const response = await clearAllCache();
      
      if (response.success) {
        onToast && onToast(response.message, 'success');
        
        // 清除所有缓存后重新加载页面
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        onToast && onToast(response.message, 'error');
      }
    } catch (error) {
      console.error('清除所有缓存失败:', error);
      onToast && onToast('清除所有缓存失败', 'error');
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
        className="w-full max-w-md rounded-lg shadow-xl max-h-[90vh] min-h-[300px] overflow-hidden flex flex-col"
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 - 紧凑设计 */}
        <div className="px-4 py-3 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-base sm:text-lg font-semibold">缓存管理</h2>
            <button
              onClick={onClose}
              className="p-1 rounded-md hover:bg-gray-100 transition-colors"
            >
              <span className="text-lg">×</span>
            </button>
          </div>
          <p className="text-xs sm:text-sm opacity-70 mt-1">
            选择要清除的缓存类型
          </p>
        </div>

        {/* 内容区域 - 可滚动，自适应高度 */}
        <div className="px-4 py-3 flex-1 overflow-y-auto min-h-0">
          {isLoadingTypes ? (
            <div className="text-center py-4 text-sm opacity-70">
              加载中...
            </div>
          ) : (
            <div className="space-y-3">
              {/* 全选按钮 */}
              <div className="flex items-center justify-between mb-4">
                <button
                  onClick={toggleSelectAll}
                  className="text-sm px-3 py-1 rounded text-blue-600 hover:bg-blue-50 transition-colors"
                >
                  {selectedTypes.length === Object.keys(cacheTypes).length ? '全不选' : '全选'}
                </button>
                <span className="text-xs opacity-70">
                  已选择 {selectedTypes.length} / {Object.keys(cacheTypes).length}
                </span>
              </div>

              {/* 缓存类型列表 */}
              {Object.entries(cacheTypes).map(([type, info]) => (
                <div 
                  key={type}
                  className="border rounded-md p-3 cursor-pointer hover:bg-gray-50 transition-colors"
                  style={{ borderColor: themeParams?.hint_color + '20' || '#e5e7eb' }}
                  onClick={() => toggleCacheType(type)}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={selectedTypes.includes(type)}
                      onChange={() => toggleCacheType(type)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium">
                        {info.name}
                      </div>
                      <div className="text-xs opacity-70 mt-1">
                        {info.description}
                      </div>
                      {info.warning && (
                        <div className="text-xs text-orange-600 mt-1">
                          ⚠️ {info.warning}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 底部操作 - 固定在底部，响应式布局 */}
        <div className="px-4 py-3 border-t border-gray-200 flex-shrink-0">
          <div className="space-y-2">
            {/* 清除按钮行 - 在超短屏幕上可以垂直排列 */}
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={showClearSelectedConfirm}
                disabled={isLoading || selectedTypes.length === 0}
                className="flex-1 px-3 py-2 rounded-md text-xs sm:text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[36px]"
                style={buttonStyle}
              >
                {isLoading ? '清除中...' : '清除选中'}
              </button>
              <button
                onClick={showClearAllConfirm}
                disabled={isLoading}
                className="flex-1 px-3 py-2 rounded-md text-xs sm:text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[36px]"
                style={dangerButtonStyle}
              >
                {isLoading ? '清除中...' : '清除全部'}
              </button>
            </div>
            {/* 关闭按钮行 - 紧凑设计 */}
            <button
              onClick={onClose}
              className="w-full px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium bg-gray-500 text-white hover:bg-gray-600 transition-colors min-h-[32px]"
            >
              关闭
            </button>
          </div>
        </div>
      </div>

      {/* 确认对话框 */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        confirmText="确认清除"
        cancelText="取消"
        type="danger"
        onConfirm={handleConfirmAction}
        onCancel={handleCancelAction}
      />
    </div>
  );
};

export default CacheManagement;