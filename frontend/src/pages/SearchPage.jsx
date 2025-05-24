import { useEffect } from 'react';
import SearchBar from '../components/SearchBar';
import FilterControls from '../components/FilterControls';
import ResultsList from '../components/ResultsList';
import useSearchStore from '../store/searchStore';
import useTelegramSDK from '../hooks/useTelegramSDK';

/**
 * 搜索页面组件
 * 作为主要的搜索界面，组合搜索栏和结果列表
 */
function SearchPage() {
  const {
    query,
    fetchResults,
    isLoading
  } = useSearchStore();

  // 使用自定义TMA SDK钩子
  const {
    isInitialized,
    isAvailable,
    setMainButtonText,
    showMainButton,
    hideMainButton,
    setMainButtonClickHandler,
    triggerHapticFeedback,
    themeParams
  } = useTelegramSDK();

  // 管理MainButton状态和事件
  useEffect(() => {
    // 只在TMA环境中处理MainButton
    if (!isInitialized || !isAvailable) return;
    
    try {
      // 根据查询词状态设置主按钮文本和可见性
      if (query.trim()) {
        setMainButtonText(isLoading ? '搜索中...' : '开始搜索');
        showMainButton();
      } else {
        setMainButtonText('请输入关键词');
        hideMainButton();
      }
    } catch (error) {
      console.error('更新MainButton状态失败:', error);
    }
  }, [
    isInitialized,
    isAvailable,
    query,
    isLoading,
    setMainButtonText,
    showMainButton,
    hideMainButton
  ]);

  // 设置MainButton点击事件
  useEffect(() => {
    // 只在TMA环境中设置点击事件
    if (!isInitialized || !isAvailable) return;
    
    try {
      const handleMainButtonClick = () => {
        if (query.trim() && !isLoading) {
          fetchResults();
          // 尝试触发触觉反馈
          try {
            triggerHapticFeedback('impact');
          } catch (hapticError) {
            console.warn('触发触觉反馈失败，但继续执行:', hapticError);
          }
        }
      };
      
      // 设置点击处理程序并返回清理函数
      return setMainButtonClickHandler(handleMainButtonClick);
    } catch (error) {
      console.error('设置MainButton点击事件失败:', error);
      return () => {}; // 返回空函数作为清理函数
    }
  }, [
    isInitialized,
    isAvailable,
    query,
    isLoading,
    fetchResults,
    setMainButtonClickHandler,
    triggerHapticFeedback
  ]);

  // 动态header样式
  const headerStyle = isAvailable && themeParams ? {
    color: themeParams.text_color
  } : {};

  const gradientStyle = isAvailable && themeParams ? {
    background: `linear-gradient(to right, ${themeParams.button_color || '#2481cc'}, ${themeParams.link_color || '#04a79a'})`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    color: 'transparent'
  } : {
    background: 'linear-gradient(to right, #3b82f6, #2dd4bf)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    color: 'transparent'
  };

  const subtitleStyle = isAvailable && themeParams ? {
    color: themeParams.hint_color
  } : {
    color: 'rgb(107 114 128)'
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <header className="mb-8 text-center" style={headerStyle}>
        <h1 className="text-3xl font-bold" style={gradientStyle}>
          Telegram 中文历史消息搜索
        </h1>
        <p className="mt-2" style={subtitleStyle}>
          在您的Telegram历史消息中快速查找信息
        </p>
      </header>

      <main>
        {/* 搜索栏 */}
        <SearchBar />
        
        {/* 筛选控件 */}
        <FilterControls />
        
        {/* 搜索结果列表 */}
        <ResultsList />
      </main>
    </div>
  );
}

export default SearchPage;