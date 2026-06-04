// Global State
let currentPage = 1;
const limitPerPage = 15;
let totalReviewsCount = 0;

let chartTimeSeries = null;
let chartCategories = null;

// API Endpoints
const API_SUMMARY = "/api/summary";
const API_REVIEWS = "/api/reviews";

// Helper: Format rating stars
function getRatingStars(rating) {
  // If rating is 0 or 1, we show a binary indicator or mock stars
  if (rating === 1) {
    return "★ ★ ★ ★ ★";
  } else if (rating === 0) {
    return "★ ★ ☆ ☆ ☆";
  }
  
  // Normal star display if 1-5 scale exists
  let stars = "";
  for (let i = 1; i <= 5; i++) {
    stars += i <= rating ? "★ " : "☆ ";
  }
  return stars.trim();
}

// Fetch and load summary metrics & charts
async function loadSummary() {
  try {
    const res = await fetch(API_SUMMARY);
    if (!res.ok) throw new Error("Không thể tải thông tin thống kê.");
    const data = await res.json();
    
    // Update KPI Card values
    document.getElementById("val-total-reviews").innerText = data.total_reviews.toLocaleString();
    document.getElementById("val-total-aspects").innerText = `${data.total_aspects.toLocaleString()} khía cạnh`;
    
    document.getElementById("val-avg-sentiment").innerText = data.avg_sentiment;
    
    // Position the sentiment progress bar
    // Scale from -1.0 to 1.0 (map to 0% to 100%)
    const pct = ((data.avg_sentiment + 1) / 2) * 100;
    document.getElementById("sentiment-bar").style.width = `${pct}%`;
    
    // Rankings
    if (data.branch_risk_ranking && data.branch_risk_ranking.length > 0) {
      const worst = data.branch_risk_ranking[0];
      document.getElementById("val-worst-branch").innerText = worst.branch_name;
      document.getElementById("val-worst-score").innerText = `Risk Score: ${worst.risk_score}`;
    }
    
    if (data.branch_strength_ranking && data.branch_strength_ranking.length > 0) {
      const best = data.branch_strength_ranking[0];
      document.getElementById("val-best-branch").innerText = best.branch_name;
      document.getElementById("val-best-score").innerText = `Strength Score: ${best.strength_score}`;
    }
    
    // Render Charts
    renderTimeSeriesChart(data.time_series);
    renderCategoryChart(data.category_counts);
    
    // Render Tables
    renderTopComplaints(data.top_complaints);
    renderEmergingIssues(data.emerging_issues);
    
  } catch (error) {
    console.error("Summary error:", error);
  }
}

// Render xu hướng thời gian Chart
function renderTimeSeriesChart(seriesData) {
  const dates = seriesData.map(item => item.date);
  const volumes = seriesData.map(item => item.volume);
  const sentiments = seriesData.map(item => item.avg_sentiment);

  const options = {
    series: [
      {
        name: 'Tần suất phản hồi',
        type: 'column',
        data: volumes
      },
      {
        name: 'Sentiment trung bình',
        type: 'line',
        data: sentiments
      }
    ],
    chart: {
      height: 350,
      type: 'line',
      background: 'transparent',
      toolbar: { show: false },
      foreColor: '#9ca3af'
    },
    grid: {
      borderColor: 'rgba(255,255,255,0.05)',
      xaxis: { lines: { show: true } }
    },
    stroke: {
      width: [0, 3],
      curve: 'smooth'
    },
    plotOptions: {
      bar: {
        columnWidth: '50%',
        borderRadius: 4
      }
    },
    colors: ['#06b6d4', '#10b981'],
    fill: {
      opacity: [0.35, 1],
      gradient: {
        inverseColors: false,
        shade: 'dark',
        type: "vertical",
        opacityFrom: 0.85,
        opacityTo: 0.55
      }
    },
    labels: dates,
    markers: {
      size: [0, 4]
    },
    xaxis: {
      type: 'datetime',
      axisBorder: { show: false },
      axisTicks: { show: false }
    },
    yaxis: [
      {
        title: {
          text: 'Phản hồi',
          style: { color: '#06b6d4' }
        }
      },
      {
        opposite: true,
        title: {
          text: 'Sentiment Score',
          style: { color: '#10b981' }
        },
        min: -1.0,
        max: 1.0
      }
    ],
    tooltip: {
      theme: 'dark'
    },
    legend: {
      position: 'top',
      horizontalAlign: 'right'
    }
  };

  if (chartTimeSeries) {
    chartTimeSeries.destroy();
  }
  chartTimeSeries = new ApexCharts(document.querySelector("#chart-time-series"), options);
  chartTimeSeries.render();
}

// Render category breakdown donut chart
function renderCategoryChart(counts) {
  const labels = Object.keys(counts);
  const values = Object.values(counts);

  const options = {
    series: values,
    chart: {
      type: 'donut',
      height: 350,
      background: 'transparent',
      foreColor: '#9ca3af'
    },
    labels: labels,
    colors: ['#10b981', '#06b6d4', '#fbbf24', '#f43f5e', '#6b7280'],
    stroke: {
      show: true,
      colors: ['#0b0f19'],
      width: 3
    },
    plotOptions: {
      pie: {
        donut: {
          size: '70%',
          background: 'transparent',
          labels: {
            show: true,
            name: { show: true },
            value: {
              show: true,
              fontSize: '1.5rem',
              fontWeight: 700,
              color: '#ffffff'
            },
            total: {
              show: true,
              label: 'Tổng khía cạnh',
              color: '#9ca3af'
            }
          }
        }
      }
    },
    legend: {
      position: 'bottom'
    },
    tooltip: {
      theme: 'dark'
    }
  };

  if (chartCategories) {
    chartCategories.destroy();
  }
  chartCategories = new ApexCharts(document.querySelector("#chart-categories"), options);
  chartCategories.render();
}

// Render Top Complaints table
function renderTopComplaints(complaints) {
  const tbody = document.getElementById("table-complaints-body");
  if (!complaints || complaints.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="loading-cell">Không có khiếu nại nghiêm trọng nào.</td></tr>`;
    return;
  }
  
  tbody.innerHTML = complaints.map(c => {
    const trendClass = c.trend_pct > 0 ? "warning-text" : "success-text";
    const trendSign = c.trend_pct > 0 ? "+" : "";
    return `
      <tr>
        <td style="font-weight: 600;">${c.subcategory}</td>
        <td>${c.mentions} <span class="${trendClass}" style="font-size:0.75rem; margin-left:5px;">(${trendSign}${c.trend_pct}%)</span></td>
        <td style="color: #f43f5e; font-weight: 700;">${c.impact_score}</td>
        <td style="font-size: 0.8rem; color: #9ca3af;">${c.affected_branches.join(", ")}</td>
      </tr>
    `;
  }).join("");
}

// Render Emerging Issues cards
function renderEmergingIssues(issues) {
  const container = document.getElementById("emerging-container");
  if (!issues || issues.length === 0) {
    container.innerHTML = `<div class="empty-state">Chưa phát hiện thấy bất thường nghiêm trọng nào trong 7 ngày qua.</div>`;
    return;
  }
  
  container.innerHTML = issues.map(i => `
    <div class="emerging-item">
      <div class="emerging-title-row">
        <span class="emerging-title">🚨 ${i.subcategory}</span>
        <span class="emerging-growth">+${i.growth_rate_pct}% Growth</span>
      </div>
      <div class="emerging-details">
        <span>Tần suất tuần này: <strong>${i.current_mentions}</strong> (so với ${i.previous_mentions} tuần trước)</span>
        <span>Severity TB: <strong style="color:#fbbf24;">${i.avg_severity}/5</strong></span>
      </div>
      <div class="emerging-quote">
        <strong>Ví dụ phản hồi:</strong> "${i.evidence}"
      </div>
    </div>
  `).join("");
}

// Fetch and load reviews feed
async function loadReviews() {
  const feedContainer = document.getElementById("reviews-feed-container");
  feedContainer.innerHTML = `<div class="loading-state">Đang tải phản hồi...</div>`;
  
  // Build query parameters
  const branch = document.getElementById("filter-branch").value;
  const category = document.getElementById("filter-category").value;
  const sentiment = document.getElementById("filter-sentiment").value;
  const source = document.getElementById("filter-source").value;
  const search = document.getElementById("search-input").value;
  
  let url = `${API_REVIEWS}?page=${currentPage}&limit=${limitPerPage}`;
  if (branch && branch !== "all") url += `&branch=${encodeURIComponent(branch)}`;
  if (category && category !== "all") url += `&category=${encodeURIComponent(category)}`;
  if (sentiment && sentiment !== "all") url += `&sentiment=${encodeURIComponent(sentiment)}`;
  if (source && source !== "all") url += `&source=${encodeURIComponent(source)}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Không thể tải danh sách reviews.");
    const data = await res.json();
    
    totalReviewsCount = data.total;
    
    // Update pagination labels & states
    document.getElementById("page-info-label").innerText = `Trang ${data.page} / ${Math.ceil(data.total / limitPerPage) || 1} (Tổng: ${data.total})`;
    document.getElementById("btn-prev-page").disabled = data.page <= 1;
    document.getElementById("btn-next-page").disabled = data.page >= Math.ceil(data.total / limitPerPage);
    
    if (data.reviews.length === 0) {
      feedContainer.innerHTML = `<div class="empty-state">Không tìm thấy phản hồi nào trùng khớp với bộ lọc.</div>`;
      return;
    }
    
    feedContainer.innerHTML = data.reviews.map(r => {
      const isPositive = r.sentiment > 0;
      const isNegative = r.sentiment < 0;
      
      const sentimentTag = isPositive 
        ? `<span class="tag tag-sentiment-pos">Tích cực (${r.sentiment})</span>` 
        : isNegative 
          ? `<span class="tag tag-sentiment-neg">Tiêu cực (${r.sentiment})</span>` 
          : `<span class="tag tag-sentiment-neutral">Trung lập (${r.sentiment})</span>`;
          
      const severityTag = isNegative 
        ? `<span class="tag tag-severity">Severity: ${r.severity}/5</span>` 
        : "";

      // Format timestamp
      let dateFormatted = r.created_at;
      try {
        const d = new Date(r.created_at);
        dateFormatted = d.toLocaleString('vi-VN');
      } catch(e) {}
      
      // Parse source badge
      const source = r.source || "unknown";
      const sourceBadge = `<span class="badge-source">${source.toUpperCase()}</span>`;

      return `
        <div class="review-card">
          <div class="review-card-header">
            <div class="review-meta-left">
              <span class="review-id">${r.review_id}</span>
              <span class="review-branch">📍 ${r.branch_name}</span>
              <span class="review-date">${dateFormatted}</span>
            </div>
            <div class="review-meta-right">
              ${sourceBadge}
              <span class="rating-stars">${getRatingStars(r.rating)}</span>
            </div>
          </div>
          <div class="review-content">
            ${r.content || r.evidence}
          </div>
          ${r.evidence && r.content && r.evidence !== r.content ? `
          <div class="review-evidence" style="font-size:0.85rem; background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:6px; margin:8px 0 12px 0; border-left: 3px solid var(--accent); color:var(--text-secondary); font-style:italic;">
            <strong>Bằng chứng (Evidence):</strong> "${r.evidence}"
          </div>
          ` : ''}
          <div class="review-analysis-tags">
            <span class="tag tag-category">${r.main_category}</span>
            <span class="tag tag-sub">${r.subcategory}</span>
            ${sentimentTag}
            ${severityTag}
            <span class="tag" style="background:rgba(255,255,255,0.02); color:var(--text-secondary);">Độ tự tin: ${Math.round(r.confidence * 100)}%</span>
          </div>
        </div>
      `;
    }).join("");
    
  } catch (error) {
    feedContainer.innerHTML = `<div class="error-state">Có lỗi xảy ra: ${error.message}</div>`;
  }
}

// Hook up event listeners for filtering
function setupEventListeners() {
  // Filter triggers
  document.getElementById("filter-branch").addEventListener("change", () => {
    currentPage = 1;
    loadReviews();
  });
  
  document.getElementById("filter-category").addEventListener("change", () => {
    currentPage = 1;
    loadReviews();
  });
  
  document.getElementById("filter-sentiment").addEventListener("change", () => {
    currentPage = 1;
    loadReviews();
  });
  
  document.getElementById("filter-source").addEventListener("change", () => {
    currentPage = 1;
    loadReviews();
  });
  
  // Search triggers
  document.getElementById("search-btn").addEventListener("click", () => {
    currentPage = 1;
    loadReviews();
  });
  
  document.getElementById("search-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      currentPage = 1;
      loadReviews();
    }
  });
  
  // Pagination
  document.getElementById("btn-prev-page").addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage--;
      loadReviews();
      document.querySelector(".reviews-section").scrollIntoView({ behavior: 'smooth' });
    }
  });
  
  document.getElementById("btn-next-page").addEventListener("click", () => {
    if (currentPage < Math.ceil(totalReviewsCount / limitPerPage)) {
      currentPage++;
      loadReviews();
      document.querySelector(".reviews-section").scrollIntoView({ behavior: 'smooth' });
    }
  });
}

// Initial Load
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadSummary();
  loadReviews();
});
