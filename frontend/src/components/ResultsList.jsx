import { useEffect } from 'react';
import useSearchStore from '../store/searchStore';
import useTelegramSDK from '../hooks/useTelegramSDK';
import ResultItem from './ResultItem';

/**
 * 搜索结果列表组件
 * 显示搜索结果，处理分页，展示不同状态（加载中、无结果、错误）
 */
function ResultsList() {
  // 从store获取状态和actions
  const {
    results,
    isLoading,
    error,
    pagination,
    setPage,
    fetchResults
  } = useSearchStore();

  // 使用TMA SDK钩子
  const {
    isAvailable,
    themeParams,
    triggerHapticFeedback
  } = useTelegramSDK();

  // 解构分页信息
  const { currentPage, totalPages, totalHits, hitsPerPage } = pagination;

  // 计算当前显示的结果范围
  const startItem = (currentPage - 1) * hitsPerPage + 1;
  const endItem = Math.min(currentPage * hitsPerPage, totalHits);

  /**
   * 处理页码变更
   * @param {number} newPage - 新的页码
   */
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages && newPage !== currentPage) {
      setPage(newPage);
      fetchResults(); // 使用store中已有的query和filters
      
      // 触发触觉反馈
      triggerHapticFeedback('selection');
      
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // 标题元素 - 条件渲染
  const renderTitle = () => {
    if (error) return null; // 出错时不显示标题
    if (isLoading && !results.length) return null; // 首次加载时不显示标题
    if (!results.length) return null; // 无结果时不显示标题

    // 根据Telegram主题设置文本颜色
    const textStyle = isAvailable && themeParams
      ? { color: themeParams.hint_color }
      : {};

    return (
      <div className="mb-4 text-sm" style={textStyle}>
        {totalHits > 0 ? (
          <p>
            共 {totalHits} 条结果，当前显示第 {startItem}-{endItem} 条
          </p>
        ) : (
          <p>无搜索结果</p>
        )}
      </div>
    );
  };

  // 分页导航元素 - 当有多页结果时显示
  const renderPagination = () => {
    // 当估计总结果数正好等于每页显示数量时，可能是API限制了返回的结果数
    // 在这种情况下，即使totalPages=1，也显示分页，以便用户可以尝试查看更多结果
    const apiLimitedResults = totalHits > 0 && totalHits === hitsPerPage;
    
    if (totalPages <= 1 && !apiLimitedResults) return null;

    // 设置Telegram主题样式
    const buttonStyle = isAvailable && themeParams ? {
      border: `1px solid ${themeParams.hint_color}`,
      color: themeParams.text_color
    } : {};

    const paginationTextStyle = isAvailable && themeParams ? {
      color: themeParams.text_color
    } : {};

    return (
      <div className="flex justify-center items-center mt-6 space-x-2">
        {/* 上一页按钮 */}
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1 rounded border disabled:opacity-50 disabled:cursor-not-allowed"
          style={buttonStyle}
          aria-label="上一页"
        >
          ← 上一页
        </button>

        {/* 页码指示器 */}
        <span className="px-3 py-1" style={paginationTextStyle}>
          {currentPage} / {totalPages}
        </span>

        {/* 下一页按钮 */}
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 rounded border disabled:opacity-50 disabled:cursor-not-allowed"
          style={buttonStyle}
          aria-label="下一页"
        >
          下一页 →
        </button>
      </div>
    );
  };

  // Telegram主题下的加载动画样式
  const loadingSpinnerStyle = isAvailable && themeParams ? {
    borderTopColor: themeParams.button_color,
    borderBottomColor: themeParams.button_color
  } : {
    borderTopColor: 'rgb(59 130 246)',
    borderBottomColor: 'rgb(59 130 246)'
  };

  // 错误消息样式
  const errorStyle = isAvailable && themeParams ? {
    backgroundColor: 'rgba(254, 226, 226, 0.5)',
    borderColor: 'rgb(252, 165, 165)',
    color: 'rgb(185, 28, 28)'
  } : {};

  // 无结果状态样式
  const noResultsStyle = isAvailable && themeParams ? {
    backgroundColor: themeParams.secondary_bg_color,
    color: themeParams.hint_color
  } : {};

  return (
    <div className="w-full">
      {/* 标题区域 */}
      {renderTitle()}

      {/* 加载状态 */}
      {isLoading && (
        <div className="flex justify-center my-8">
          <div
            className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2"
            style={loadingSpinnerStyle}
          ></div>
        </div>
      )}

      {/* 错误状态 */}
      {error && !isLoading && (
        <div
          className="border px-4 py-3 rounded mb-4"
          style={errorStyle}
        >
          <p className="font-bold">搜索出错</p>
          <p>{error}</p>
        </div>
      )}

      {/* 无结果状态 */}
      {!isLoading && !error && results.length === 0 && (
        <div
          className="text-center py-12 rounded-lg"
          style={noResultsStyle}
        >
          <p>
            未找到匹配的结果，请尝试其他关键词
          </p>
        </div>
      )}

      {/* 结果列表 */}
      {!isLoading && !error && results.length > 0 && (
        <div className="space-y-4">
          {results.map((result) => (
            <ResultItem key={result.id || `result-${Math.random()}`} result={result} />
          ))}
        </div>
      )}

      {/* 分页控件 */}
      {!isLoading && !error && renderPagination()}
    </div>
  );
}

export default ResultsList;