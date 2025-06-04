import useTheme from '../../hooks/useTheme';
import ThemeToggle from './ThemeToggle';

/**
 * 主题演示组件
 * 展示不同主题下的UI元素效果
 */
const ThemeDemo = () => {
  const { resolvedTheme, getThemeDisplayName, theme } = useTheme();

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* 标题区域 */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-text-primary mb-2">
          主题系统演示
        </h1>
        <p className="text-text-secondary mb-4">
          当前主题: {getThemeDisplayName(theme)} 
          {theme === 'system' && ` (解析为: ${getThemeDisplayName(resolvedTheme)})`}
        </p>
        <div className="flex justify-center space-x-4">
          <ThemeToggle mode="simple" size="large" />
          <ThemeToggle mode="detailed" size="medium" />
        </div>
      </div>

      {/* 色彩展示区域 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 背景色卡片 */}
        <div className="bg-bg-secondary border border-border-primary rounded-lg p-4 transition-theme">
          <h3 className="text-lg font-semibold text-text-primary mb-3">背景色</h3>
          <div className="space-y-2">
            <div className="bg-bg-primary border border-border-secondary rounded p-2">
              <span className="text-text-secondary text-sm">主背景</span>
            </div>
            <div className="bg-bg-secondary border border-border-secondary rounded p-2">
              <span className="text-text-secondary text-sm">次背景</span>
            </div>
            <div className="bg-bg-tertiary border border-border-secondary rounded p-2">
              <span className="text-text-secondary text-sm">三级背景</span>
            </div>
          </div>
        </div>

        {/* 文字色卡片 */}
        <div className="bg-bg-secondary border border-border-primary rounded-lg p-4 transition-theme">
          <h3 className="text-lg font-semibold text-text-primary mb-3">文字色</h3>
          <div className="space-y-2">
            <p className="text-text-primary">主要文字</p>
            <p className="text-text-secondary">次要文字</p>
            <p className="text-text-tertiary">辅助文字</p>
          </div>
        </div>

        {/* 交互元素卡片 */}
        <div className="bg-bg-secondary border border-border-primary rounded-lg p-4 transition-theme">
          <h3 className="text-lg font-semibold text-text-primary mb-3">交互元素</h3>
          <div className="space-y-3">
            <button className="w-full bg-accent-primary text-white px-4 py-2 rounded-md hover:bg-accent-hover transition-theme">
              主要按钮
            </button>
            <button className="w-full border border-border-primary text-text-primary px-4 py-2 rounded-md hover:bg-bg-tertiary transition-theme">
              次要按钮
            </button>
          </div>
        </div>

        {/* 状态色卡片 */}
        <div className="bg-bg-secondary border border-border-primary rounded-lg p-4 transition-theme">
          <h3 className="text-lg font-semibold text-text-primary mb-3">状态色</h3>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-success rounded-full"></div>
              <span className="text-success">成功状态</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-warning rounded-full"></div>
              <span className="text-warning">警告状态</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-error rounded-full"></div>
              <span className="text-error">错误状态</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-info rounded-full"></div>
              <span className="text-info">信息状态</span>
            </div>
          </div>
        </div>

        {/* 表单元素卡片 */}
        <div className="bg-bg-secondary border border-border-primary rounded-lg p-4 transition-theme">
          <h3 className="text-lg font-semibold text-text-primary mb-3">表单元素</h3>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="输入框"
              className="w-full px-3 py-2 border border-border-primary rounded-md bg-bg-primary text-text-primary placeholder-text-tertiary focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition-theme"
            />
            <select className="w-full px-3 py-2 border border-border-primary rounded-md bg-bg-primary text-text-primary focus:ring-2 focus:ring-accent-primary focus:border-accent-primary transition-theme">
              <option>选择框</option>
              <option>选项1</option>
              <option>选项2</option>
            </select>
          </div>
        </div>

        {/* 阴影效果卡片 */}
        <div className="bg-bg-secondary border border-border-primary rounded-lg p-4 transition-theme">
          <h3 className="text-lg font-semibold text-text-primary mb-3">阴影效果</h3>
          <div className="space-y-3">
            <div className="bg-bg-primary p-3 rounded shadow-theme-sm border border-border-secondary">
              <span className="text-text-secondary text-sm">小阴影</span>
            </div>
            <div className="bg-bg-primary p-3 rounded shadow-theme-md border border-border-secondary">
              <span className="text-text-secondary text-sm">中阴影</span>
            </div>
            <div className="bg-bg-primary p-3 rounded shadow-theme-lg border border-border-secondary">
              <span className="text-text-secondary text-sm">大阴影</span>
            </div>
          </div>
        </div>
      </div>

      {/* 特性说明 */}
      <div className="bg-bg-secondary border border-border-primary rounded-lg p-6 transition-theme">
        <h3 className="text-xl font-semibold text-text-primary mb-4">主题系统特性</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-text-secondary">
          <div>
            <h4 className="font-medium text-text-primary mb-2">✨ 功能特性</h4>
            <ul className="space-y-1 text-sm">
              <li>• 支持浅色/深色/系统主题</li>
              <li>• 自动检测系统主题偏好</li>
              <li>• 主题偏好本地存储</li>
              <li>• 平滑过渡动画</li>
              <li>• 响应式设计支持</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-text-primary mb-2">🎨 设计系统</h4>
            <ul className="space-y-1 text-sm">
              <li>• 统一的颜色变量</li>
              <li>• 语义化的命名</li>
              <li>• Tailwind CSS 集成</li>
              <li>• 高对比度模式支持</li>
              <li>• 减少动画偏好支持</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeDemo; 