import { useEffect } from 'react';
import useSearchStore from '../store/searchStore';
import useTelegramSDK from '../hooks/useTelegramSDK';
import ResultItem from './ResultItem';

/**
 * 搜索结果列表组件 - 阶段3重构版本
 * 实现新的卡片式设计和现代化布局
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
  const { triggerHapticFeedback } = useTelegramSDK();

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

    return (
      <div className="results-summary">
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

    return (
      <div className="pagination">
        {/* 上一页按钮 */}
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="pagination-btn"
          aria-label="上一页"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M15 18L9 12L15 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          上一页
        </button>

        {/* 页码指示器 */}
        <div className="pagination-info">
          <span className="current-page">{currentPage}</span>
          <span className="page-separator">/</span>
          <span className="total-pages">{totalPages}</span>
        </div>

        {/* 下一页按钮 */}
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="pagination-btn"
          aria-label="下一页"
        >
          下一页
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M9 18L15 12L9 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
    );
  };

  return (
    <div className="results-list">
      {/* 标题区域 */}
      {renderTitle()}

      {/* 加载状态 */}
      {isLoading && (
        <div className="loading-state">
          <div className="loading-spinner">
            <svg className="animate-spin" width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.3"/>
              <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"/>
            </svg>
            <span>搜索中...</span>
          </div>
        </div>
      )}

      {/* 错误状态 */}
      {error && !isLoading && (
        <div className="error-state">
          <div className="error-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M15 9L9 15M9 9L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <h3 className="error-title">搜索出错</h3>
          <p className="error-message">{error}</p>
        </div>
      )}

      {/* 无结果状态 */}
      {!isLoading && !error && results.length === 0 && (
        <div className="no-results-state">
          <div className="no-results-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
              <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <h3 className="no-results-title">未找到匹配结果</h3>
          <p className="no-results-message">
            请尝试使用其他关键词或调整筛选条件
          </p>
        </div>
      )}

      {/* 结果列表 */}
      {!isLoading && !error && results.length > 0 && (
        <div className="results-grid">
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