import { useEffect } from 'react';
import useTelegramSDK from '../hooks/useTelegramSDK';
import useNavStore from '../store/navStore';
import useSettingsStore from '../store/settingsStore';
import SettingsCard from '../components/settings/SettingsCard';
import { 
  SettingsNavigationItem, 
  SettingsToggleItem, 
  SettingsSelectItem,
  SettingsInfoItem 
} from '../components/settings/SettingsItems';

/**
 * 设置页面组件
 * 包含各种设置项，使用卡片式布局
 */
function SettingsPage() {
  const { isAvailable, themeParams } = useTelegramSDK();
  const { setActiveNav } = useNavStore();
  
  // 从设置store中获取状态和方法
  const {
    appearance,
    sync,
    notifications,
    setTheme,
    setSyncFrequency,
    setHistoryRange,
    setNotificationsEnabled,
    clearCache
  } = useSettingsStore();
  
  // 页面样式
  const pageStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.bg_color
  } : {
    backgroundColor: '#f9fafb'
  };
  
  // 标题样式
  const titleStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};
  
  // 格式化上次同步时间的显示
  const formatLastSyncTime = () => {
    if (!sync.lastSyncTime) return '尚未同步';
    
    const date = new Date(sync.lastSyncTime);
    const formattedDate = date.toLocaleDateString('zh-CN');
    const formattedTime = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    return `${formattedDate} ${formattedTime} - ${sync.lastSyncStatus === 'success' ? '成功' : '失败'}`;
  };
  
  // 主题选择项
  const themeOptions = [
    { value: 'light', label: '浅色模式' },
    { value: 'dark', label: '深色模式' },
    { value: 'auto', label: '跟随系统' }
  ];
  
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
  
  // 处理清除缓存事件
  const handleClearCache = async () => {
    // 这里应该添加确认对话框
    // 简化版先直接调用清除方法
    try {
      const result = await clearCache();
      if (result.success) {
        alert(result.message); // 临时使用alert，后期可改为更友好的提示
      }
    } catch (error) {
      console.error('清除缓存失败:', error);
    }
  };
  
  // 处理白名单管理导航
  const handleNavigateToWhitelist = () => {
    // TODO: 实现白名单管理页面的导航
    alert('白名单管理功能尚未实现');
  };
  
  return (
    <div className="pb-16 w-full max-w-4xl mx-auto" style={pageStyle}>
      {/* 页面标题 */}
      <header className="px-4 py-4 flex items-center">
        <h1 className="text-xl font-medium" style={titleStyle}>设置</h1>
      </header>
      
      {/* 设置内容区域 */}
      <div className="px-4">
        {/* 个性化卡片 */}
        <SettingsCard title="个性化">
          <SettingsSelectItem
            icon="🎨"
            label="外观主题"
            description="选择应用的显示主题"
            value={appearance.theme}
            options={themeOptions}
            onChange={setTheme}
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
        </SettingsCard>
        
        {/* 数据与安全卡片 */}
        <SettingsCard title="数据与安全">
          <SettingsNavigationItem
            icon="🛡️"
            label="白名单管理"
            description="管理允许访问的IP或域名"
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
    </div>
  );
}

export default SettingsPage;