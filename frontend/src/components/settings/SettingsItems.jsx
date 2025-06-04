import { useState } from 'react';
import useTelegramSDK from '../../hooks/useTelegramSDK';

/**
 * 设置项基础组件 - 提供通用的布局和样式
 */
const SettingsItemBase = ({ icon, label, description, children, onClick }) => {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  return (
    <div 
      className={`flex items-center px-4 py-3 transition-theme ${onClick ? 'cursor-pointer active:bg-bg-tertiary' : ''}`}
      onClick={onClick}
    >
      {/* 图标区域 */}
      {icon && (
        <div className="mr-3 text-xl">
          {icon}
        </div>
      )}
      
      {/* 文本区域 */}
      <div className="flex-1">
        <div className="text-sm font-medium text-text-primary transition-theme">{label}</div>
        {description && (
          <div className="text-xs mt-0.5 text-text-secondary transition-theme">{description}</div>
        )}
      </div>
      
      {/* 控件区域 */}
      {children}
    </div>
  );
};

/**
 * 导航类型设置项 - 点击后跳转到其他页面
 */
export const SettingsNavigationItem = ({ 
  icon, 
  label, 
  description, 
  onNavigate 
}) => {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  return (
    <SettingsItemBase 
      icon={icon} 
      label={label} 
      description={description}
      onClick={onNavigate}
    >
      {/* 右箭头图标 */}
      <div className="text-text-secondary transition-theme">
        <span className="text-lg">›</span>
      </div>
    </SettingsItemBase>
  );
};

/**
 * 开关类型设置项 - 包含可切换的开关控件
 */
export const SettingsToggleItem = ({ 
  icon, 
  label, 
  description, 
  value, 
  onChange 
}) => {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  // 处理开关切换
  const handleToggle = () => {
    onChange(!value);
  };
  
  // 开关样式
  const toggleBaseStyle = {
    width: '36px',
    height: '20px',
    borderRadius: '10px',
    transition: 'background-color 0.2s'
  };
  
  // 开关滑块样式
  const toggleKnobStyle = {
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    backgroundColor: '#ffffff',
    transform: value ? 'translateX(16px)' : 'translateX(2px)',
    transition: 'transform 0.2s'
  };
  
  // 根据Telegram主题或开关状态确定颜色
  const toggleColor = isAvailable && themeParams
    ? (value ? themeParams.button_color : themeParams.hint_color + '50')
    : (value ? '#3b82f6' : '#d1d5db');
  
  return (
    <SettingsItemBase 
      icon={icon} 
      label={label} 
      description={description}
      onClick={handleToggle}
    >
      {/* 自定义开关控件 */}
      <div 
        style={{
          ...toggleBaseStyle,
          backgroundColor: toggleColor
        }}
        className="flex items-center"
      >
        <div style={toggleKnobStyle}></div>
      </div>
    </SettingsItemBase>
  );
};

/**
 * 选择类型设置项 - 点击后显示选择器
 */
export const SettingsSelectItem = ({ 
  icon, 
  label, 
  description, 
  value, 
  options, 
  onChange 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { isAvailable, themeParams, triggerHapticFeedback } = useTelegramSDK();
  
  // 当前选中项的显示值
  const selectedOption = options.find(opt => opt.value === value);
  const displayValue = selectedOption ? selectedOption.label : '';
  
  // 处理点击事件 - 打开/关闭选择器
  const handleClick = () => {
    setIsOpen(!isOpen);
    
    // 尝试触发轻微的触觉反馈
    try {
      if (isAvailable) {
        triggerHapticFeedback('light');
      }
    } catch (error) {
      console.warn('触发触觉反馈失败，但继续执行:', error);
    }
  };
  
  // 处理选择事件
  const handleSelect = (optionValue) => {
    onChange(optionValue);
    setIsOpen(false);
    
    // 尝试触发触觉反馈
    try {
      if (isAvailable) {
        triggerHapticFeedback('medium');
      }
    } catch (error) {
      console.warn('触发触觉反馈失败，但继续执行:', error);
    }
  };
  
  return (
    <div className="relative">
      <SettingsItemBase 
        icon={icon} 
        label={label} 
        description={description}
        onClick={handleClick}
      >
        {/* 当前选中值 */}
        <div className="text-sm text-text-secondary transition-theme">
          {displayValue}
        </div>
      </SettingsItemBase>
      
      {/* 选择器弹出层 */}
      {isOpen && (
        <div className="absolute bottom-full left-0 right-0 z-10 mt-1 rounded-md overflow-hidden bg-bg-primary border border-border-primary shadow-theme-lg transition-theme">
          <div className="max-h-60 overflow-auto">
            {options.map(option => (
              <div
                key={option.value}
                className={`px-4 py-2 cursor-pointer transition-theme ${
                  option.value === value 
                    ? 'bg-accent-primary/10 text-accent-primary' 
                    : 'text-text-primary hover:bg-bg-tertiary'
                }`}
                onClick={() => handleSelect(option.value)}
              >
                {option.label}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * 信息类型设置项 - 仅显示信息，不可交互
 */
export const SettingsInfoItem = ({ 
  icon, 
  label, 
  description, 
  value 
}) => {
  const { isAvailable, themeParams } = useTelegramSDK();
  
  return (
    <SettingsItemBase 
      icon={icon} 
      label={label} 
      description={description}
    >
      {/* 信息值 */}
      {value && (
        <div className="text-sm text-text-secondary transition-theme">
          {value}
        </div>
      )}
    </SettingsItemBase>
  );
};