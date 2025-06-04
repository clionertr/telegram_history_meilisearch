import { useState } from 'react';
import useTelegramSDK from '../hooks/useTelegramSDK';
import useSettingsStore from '../store/settingsStore';
import ThemeToggle from '../components/common/ThemeToggle';
import ThemeDemo from '../components/common/ThemeDemo';
import SettingsCard from '../components/settings/SettingsCard';
import {
  SettingsNavigationItem,
  SettingsToggleItem,
  SettingsSelectItem,
  SettingsInfoItem
} from '../components/settings/SettingsItems';
import WhitelistManagement from '../components/settings/WhitelistManagement';
import CacheManagement from '../components/settings/CacheManagement';
import SyncTimeManagement from '../components/settings/SyncTimeManagement';
import { ToastManager } from '../components/common/Toast';

/**
 * 设置页面组件
 * 包含各种设置项，使用卡片式布局
 */
function SettingsPage() {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  // 本地状态管理
  const [isWhitelistOpen, setIsWhitelistOpen] = useState(false);
  const [isCacheOpen, setIsCacheOpen] = useState(false);
  const [isSyncTimeOpen, setIsSyncTimeOpen] = useState(false);
  const [isThemeDemoOpen, setIsThemeDemoOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  
  // 从设置store中获取状态和方法
  const {
    appearance,
    sync,
    notifications,
    setTheme,
    setSyncFrequency,
    setHistoryRange,
    setNotificationsEnabled
  } = useSettingsStore();
  
  // 格式化上次同步时间的显示
  const formatLastSyncTime = () => {
    if (!sync.lastSyncTime) return '尚未同步';
    
    const date = new Date(sync.lastSyncTime);
    const formattedDate = date.toLocaleDateString('zh-CN');
    const formattedTime = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    return `${formattedDate} ${formattedTime} - ${sync.lastSyncStatus === 'success' ? '成功' : '失败'}`;
  };
  
  // 同步频率选择项
  const syncFrequencyOptions = [
    { value: 'hourly', label: '每小时' },
    { value: 'daily', label: '每天' },
    { value: 'manual', label: '手动' }
  ];
  
  // 历史数据范围选择项
  const historyRangeOptions = [
    { value: 'last7days', label: '最近7天' },
    { value: 'last30days', label: '最近30天' },
    { value: 'last90days', label: '最近90天' },
    { value: 'all', label: '全部历史' }
  ];
  
  // Toast 管理函数
  const addToast = (message, type = 'success', duration = 3000) => {
    const id = Date.now() + Math.random();
    const newToast = { id, message, type, duration };
    setToasts(prev => [...prev, newToast]);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  // 处理清除缓存事件 - 打开缓存管理界面
  const handleClearCache = () => {
    setIsCacheOpen(true);
  };
  
  // 处理白名单管理导航
  const handleNavigateToWhitelist = () => {
    setIsWhitelistOpen(true);
  };

  // 处理同步时间管理导航
  const handleNavigateToSyncTime = () => {
    setIsSyncTimeOpen(true);
  };

  // 处理主题演示导航
  const handleNavigateToThemeDemo = () => {
    setIsThemeDemoOpen(true);
  };

  // 如果主题演示打开，显示演示页面
  if (isThemeDemoOpen) {
    return (
      <div className="bg-bg-primary min-h-screen">
        <div className="sticky top-0 z-10 bg-bg-primary/95 backdrop-blur-sm border-b border-border-primary px-4 py-3">
          <button
            onClick={() => setIsThemeDemoOpen(false)}
            className="flex items-center space-x-2 text-accent-primary hover:text-accent-hover transition-theme"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>返回设置</span>
          </button>
        </div>
        <ThemeDemo />
      </div>
    );
  }
  
  return (
    <div className="pb-16 w-full max-w-4xl mx-auto bg-bg-primary text-text-primary min-h-screen transition-theme">
      {/* 页面标题 */}
      <header className="px-4 py-4 flex items-center">
        <h1 className="text-xl font-medium text-text-primary transition-theme">设置</h1>
      </header>
      
      {/* 设置内容区域 */}
      <div className="px-4">
        {/* 个性化卡片 */}
        <SettingsCard title="个性化">
          {/* 主题设置 */}
          <div className="flex items-center px-4 py-3 border-b border-border-primary last:border-b-0">
            <div className="mr-3 text-xl">🎨</div>
            <div className="flex-1">
              <div className="text-sm font-medium text-text-primary">外观主题</div>
              <div className="text-xs mt-0.5 text-text-secondary">
                选择应用的显示主题，支持跟随系统设置
              </div>
            </div>
            <div className="ml-4">
              <ThemeToggle mode="detailed" size="medium" />
            </div>
          </div>

          {/* 主题演示 */}
          <SettingsNavigationItem
            icon="🎭"
            label="主题演示"
            description="查看完整的主题系统功能和UI元素效果"
            onNavigate={handleNavigateToThemeDemo}
          />
          
          <SettingsToggleItem
            icon="🔔"
            label="通知设置"
            description="管理应用通知的接收方式"
            value={notifications.enabled}
            onChange={setNotificationsEnabled}
          />
        </SettingsCard>
        
        {/* 同步设置卡片 */}
        <SettingsCard title="同步设置">
          <SettingsSelectItem
            icon="🔄"
            label="自动同步频率"
            value={sync.frequency}
            options={syncFrequencyOptions}
            onChange={setSyncFrequency}
          />
          
          <SettingsInfoItem
            icon="ℹ️"
            label="上次同步"
            value={formatLastSyncTime()}
          />
          
          <SettingsSelectItem
            icon="🗓️"
            label="历史数据范围"
            description="设定同步数据的最早时间点"
            value={sync.historyRange}
            options={historyRangeOptions}
            onChange={setHistoryRange}
          />

          <SettingsNavigationItem
            icon="⏰"
            label="最旧同步时间管理"
            description="设置全局和特定聊天的最旧同步时间戳"
            onNavigate={handleNavigateToSyncTime}
          />
        </SettingsCard>
        
        {/* 数据与安全卡片 */}
        <SettingsCard title="数据与安全">
          <SettingsNavigationItem
            icon="🛡️"
            label="白名单管理"
            description="管理需要同步消息的聊天（用户/群组/频道）"
            onNavigate={handleNavigateToWhitelist}
          />
        </SettingsCard>
        
        {/* 存储与缓存卡片 */}
        <SettingsCard title="存储与缓存">
          <SettingsNavigationItem
            icon="🧹"
            label="清除缓存"
            onNavigate={handleClearCache}
          />
        </SettingsCard>
      </div>

      {/* 白名单管理模态框 */}
      <WhitelistManagement
        isOpen={isWhitelistOpen}
        onClose={() => setIsWhitelistOpen(false)}
        onToast={addToast}
      />

      {/* 缓存管理模态框 */}
      <CacheManagement
        isOpen={isCacheOpen}
        onClose={() => setIsCacheOpen(false)}
        onToast={addToast}
      />

      {/* 同步时间管理模态框 */}
      <SyncTimeManagement
        isOpen={isSyncTimeOpen}
        onClose={() => setIsSyncTimeOpen(false)}
        onToast={addToast}
      />

      {/* Toast 通知管理器 */}
      <ToastManager
        toasts={toasts}
        removeToast={removeToast}
      />
    </div>
  );
}

export default SettingsPage;