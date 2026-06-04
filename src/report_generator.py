#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report Generator Module — Standalone CLI utility to generate premium reports.
Generates structured Markdown and styled HTML reports from CRM operational insights.
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add the directory containing tools.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import tools
except ImportError:
    print("[Error] Cannot import tools.py. Please run this script from the workspace root or src directory.")
    sys.exit(1)


# HTML Template with custom premium styling
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo cáo Phân tích Phản hồi Khách hàng - InsightAgent</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #111827;
            --border-color: rgba(255, 255, 255, 0.05);
            --text-primary: #ffffff;
            --text-secondary: #9ca3af;
            --accent-cyan: #06b6d4;
            --accent-emerald: #10b981;
            --accent-rose: #f43f5e;
            --accent-amber: #fbbf24;
            --accent-indigo: #6366f1;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        
        /* Header style */
        .report-header {{
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(99, 102, 241, 0.1));
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header-title h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(to right, #06b6d4, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }}
        
        .header-title p {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}
        
        .badge-period {{
            background-color: var(--accent-cyan);
            color: var(--bg-color);
            font-weight: 600;
            font-size: 0.8rem;
            padding: 6px 16px;
            border-radius: 20px;
            text-transform: uppercase;
        }}
        
        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background-color: var(--accent-indigo);
        }}
        
        .kpi-card.worst::before {{ background-color: var(--accent-rose); }}
        .kpi-card.best::before {{ background-color: var(--accent-emerald); }}
        .kpi-card.period::before {{ background-color: var(--accent-amber); }}
        
        .kpi-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .kpi-value {{
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        
        .kpi-desc {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        
        /* Two columns layout */
        .columns-layout {{
            display: grid;
            grid-template-columns: 1.5fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        @media (max-width: 900px) {{
            .columns-layout {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 30px;
        }}
        
        .card-title {{
            font-size: 1.15rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
        }}
        
        .card-badge {{
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 500;
        }}
        
        .badge-danger {{ background: rgba(244, 63, 94, 0.1); color: var(--accent-rose); }}
        .badge-success {{ background: rgba(16, 185, 129, 0.1); color: var(--accent-emerald); }}
        .badge-warn {{ background: rgba(251, 191, 36, 0.1); color: var(--accent-amber); }}
        
        /* Table Styles */
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        
        th {{
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 0.85rem;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        td {{
            padding: 14px 12px;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.9rem;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        /* Emerging Issue Item */
        .emerging-item {{
            background-color: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 15px;
        }}
        
        .emerging-item:last-child {{
            margin-bottom: 0;
        }}
        
        .emerging-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .emerging-title {{
            font-weight: 600;
            color: var(--accent-amber);
            font-size: 0.95rem;
        }}
        
        .emerging-growth {{
            font-weight: 700;
            color: var(--accent-rose);
            font-size: 0.85rem;
        }}
        
        .emerging-body {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 10px;
        }}
        
        .emerging-quote {{
            font-size: 0.82rem;
            color: var(--text-secondary);
            font-style: italic;
            border-left: 2px solid var(--accent-amber);
            padding-left: 10px;
            background: rgba(251, 191, 36, 0.02);
            padding: 6px 10px;
            border-radius: 0 6px 6px 0;
        }}
        
        /* Action Item */
        .action-list {{
            list-style: none;
        }}
        
        .action-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 16px;
        }}
        
        .action-num {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--accent-indigo);
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.85rem;
            margin-right: 12px;
            flex-shrink: 0;
            margin-top: 2px;
        }}
        
        .action-text {{
            font-size: 0.92rem;
        }}
        
        .chart-wrapper {{
            min-height: 350px;
        }}
        
        .footer {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.8rem;
            margin-top: 40px;
            border-top: 1px solid var(--border-color);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="report-header">
            <div class="header-title">
                <h1>Báo cáo Insight Vận hành Khách hàng</h1>
                <p>Khởi tạo lúc: {datetime_now} · Dự án Customer Review Insight Agent</p>
            </div>
            <div>
                <span class="badge-period">Thời gian: {period_label}</span>
            </div>
        </header>

        <!-- KPI Cards -->
        <section class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Tổng khía cạnh phân tích</div>
                <div class="kpi-value">{total_aspects}</div>
                <div class="kpi-desc">Tổng số reviews: {total_reviews}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Sentiment trung bình</div>
                <div class="kpi-value" style="color: {sentiment_color};">{avg_sentiment}</div>
                <div class="kpi-desc">Thang điểm từ -1.0 đến 1.0</div>
            </div>
            <div class="kpi-card worst">
                <div class="kpi-label">Rủi ro nhất</div>
                <div class="kpi-value warning-text" style="color: var(--accent-rose);">{worst_branch}</div>
                <div class="kpi-desc">Risk Score: {worst_score}</div>
            </div>
            <div class="kpi-card best">
                <div class="kpi-label">Hài lòng nhất</div>
                <div class="kpi-value success-text" style="color: var(--accent-emerald);">{best_branch}</div>
                <div class="kpi-desc">Strength Score: {best_score}</div>
            </div>
        </section>

        <!-- Main Analytics & Charts -->
        <div class="card">
            <div class="card-title">
                <span>Xu hướng Phản hồi và Phân bổ Khía cạnh</span>
            </div>
            <div style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 20px;">
                <div class="chart-wrapper" id="chart-timeline"></div>
                <div class="chart-wrapper" id="chart-donut"></div>
            </div>
        </div>

        <!-- Risks & Emerging Issues columns -->
        <div class="columns-layout">
            <!-- Left: Top Complaints -->
            <div class="card" style="margin-bottom: 0;">
                <div class="card-title">
                    <span>Top 5 Khiếu nại Nghiêm trọng Nhất</span>
                    <span class="card-badge badge-danger">Yêu cầu xử lý</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Vấn đề (Subcategory)</th>
                            <th>Lượt nhắc</th>
                            <th>Impact Score</th>
                            <th>Chi nhánh ảnh hưởng</th>
                        </tr>
                    </thead>
                    <tbody>
                        {complaint_rows}
                    </tbody>
                </table>
            </div>

            <!-- Right: Emerging issues -->
            <div class="card" style="margin-bottom: 0;">
                <div class="card-title">
                    <span>Vấn đề Bất thường Mới (Emerging)</span>
                    <span class="card-badge badge-warn">Theo dõi sát</span>
                </div>
                <div>
                    {emerging_items}
                </div>
            </div>
        </div>

        <!-- Action Items / Recommendations -->
        <div class="card">
            <div class="card-title">
                <span>Khuyến nghị Hành động Vận hành Ưu tiên</span>
                <span class="card-badge badge-success">CSKH & Vận hành</span>
            </div>
            <ul class="action-list">
                {action_items}
            </ul>
        </div>

        <footer class="footer">
            <p>© 2026 Customer Review Insight Agent Plan. Báo cáo tự động hóa độc lập.</p>
        </footer>
    </div>

    <!-- Script to render charts using serialized python data -->
    <script>
        const chartData = {chart_data_json};

        // 1. Timeline Chart
        const timelineOptions = {{
            series: [
                {{
                    name: 'Số lượng phản hồi',
                    type: 'column',
                    data: chartData.timeline.volumes
                }},
                {{
                    name: 'Chỉ số cảm xúc',
                    type: 'line',
                    data: chartData.timeline.sentiments
                }}
            ],
            chart: {{
                height: 320,
                type: 'line',
                background: 'transparent',
                toolbar: {{ show: false }},
                foreColor: '#9ca3af'
            }},
            colors: ['#06b6d4', '#10b981'],
            stroke: {{
                width: [0, 3],
                curve: 'smooth'
            }},
            plotOptions: {{
                bar: {{
                    columnWidth: '50%',
                    borderRadius: 4
                }}
            }},
            grid: {{
                borderColor: 'rgba(255, 255, 255, 0.05)'
            }},
            xaxis: {{
                categories: chartData.timeline.dates,
                type: 'datetime',
                axisBorder: {{ show: false }},
                axisTicks: {{ show: false }}
            }},
            yaxis: [
                {{
                    title: {{ text: 'Tần suất', style: {{ color: '#06b6d4' }} }}
                }},
                {{
                    opposite: true,
                    title: {{ text: 'Sentiment', style: {{ color: '#10b981' }} }},
                    min: -1.0,
                    max: 1.0
                }}
            ],
            tooltip: {{ theme: 'dark' }},
            legend: {{ position: 'top', horizontalAlign: 'right' }}
        }};

        new ApexCharts(document.querySelector("#chart-timeline"), timelineOptions).render();

        // 2. Donut Chart
        const donutOptions = {{
            series: chartData.donut.values,
            chart: {{
                type: 'donut',
                height: 320,
                background: 'transparent',
                foreColor: '#9ca3af'
            }},
            labels: chartData.donut.labels,
            colors: ['#10b981', '#06b6d4', '#fbbf24', '#f43f5e', '#6b7280'],
            stroke: {{ show: false }},
            plotOptions: {{
                pie: {{
                    donut: {{
                        size: '65%',
                        labels: {{
                            show: true,
                            name: {{ show: true }},
                            value: {{
                                show: true,
                                fontSize: '1.2rem',
                                fontWeight: 700,
                                color: '#ffffff'
                            }},
                            total: {{
                                show: true,
                                label: 'Phân bổ',
                                color: '#9ca3af'
                            }}
                        }}
                    }}
                }}
            }},
            legend: {{ position: 'bottom' }},
            tooltip: {{ theme: 'dark' }}
        }};

        new ApexCharts(document.querySelector("#chart-donut"), donutOptions).render();
    </script>
</body>
</html>
"""


def generate_markdown(data, prioritized):
    """Generate Markdown text structure."""
    datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    period_lbl = "7 ngày qua" if data["period"] == "7d" else "30 ngày qua"

    md = f"""# Báo cáo Phân tích Phản hồi Khách hàng (InsightAgent)

**Thời gian xuất báo cáo:** {datetime_str}  
**Khoảng thời gian phân tích:** {period_lbl}  
**Dự án:** Customer Review Insight Agent Plan  

---

## 📊 Chỉ số Hiệu năng Vận hành (KPIs)

| Chỉ số | Giá trị | Chi tiết |
| :--- | :---: | :--- |
| **Tổng số khía cạnh (Aspects)** | {data.get("total_aspects", 0):,} | Từ dữ liệu reviews đã làm sạch và phân tích |
| **Chỉ số Hài lòng (Sentiment)** | {data.get("avg_sentiment", 0.0)} | Điểm cảm xúc trung bình (-1.0 đến 1.0) |
| **Chi nhánh rủi ro nhất** | **{data.get("worst_branch", {}).get("branch_name", "N/A")}** | Risk Score: {data.get("worst_branch", {}).get("risk_score", 0.0)} |
| **Chi nhánh hài lòng nhất** | **{data.get("best_branch", {}).get("branch_name", "N/A")}** | Strength Score: {data.get("best_branch", {}).get("strength_score", 0.0)} |

---

## ⚠️ Top Khiếu nại Nghiêm trọng Nhất

Dưới đây là các khiếu nại (complaints) có **Impact Score** cao nhất.

| Vấn đề | Tần suất | Trend | Impact Score | Các chi nhánh bị ảnh hưởng nhiều nhất |
| :--- | :---: | :---: | :---: | :--- |
"""
    for item in data.get("top_risks", []):
        trend_sign = "+" if item.get("trend_pct", 0) > 0 else ""
        md += f"| {item.get('subcategory')} | {item.get('mentions')} | {trend_sign}{item.get('trend_pct')}% | **{item.get('impact_score')}** | {', '.join(item.get('affected_branches', []))} |\n"

    md += """
---

## 🚨 Vấn đề Bất thường Mới nổi (Emerging Issues)

Các khía cạnh ghi nhận lượt phàn nàn **tăng trưởng đột biến** trong tuần qua:

"""
    emerging = data.get("emerging_issues", [])
    if not emerging:
        md += "*Không phát hiện bất thường nghiêm trọng mới nào.*\n"
    else:
        for idx, item in enumerate(emerging):
            md += f"""{idx+1}. **{item.get('subcategory')}**
   - **Tỷ lệ tăng trưởng:** `+{item.get('growth_rate_pct')}%`
   - **Số lượt:** {item.get('current_mentions')} (so với {item.get('previous_mentions')} tuần trước)
   - **Mức độ nghiêm trọng TB:** `{item.get('avg_severity')}/5`
   - **Trích dẫn bằng chứng:** *"{item.get('evidence')}"*\n\n"""

    md += """---

## 💡 Đề xuất Thứ tự Ưu tiên Xử lý Rủi ro

Dựa trên thuật toán tính điểm ưu tiên Impact Score:

"""
    for p in prioritized.get("prioritized_risks", []):
        md += f"- **[Độ ưu tiên {p.get('priority')}] {p.get('subcategory')}** (Impact Score: `{p.get('impact_score')}`, Severity TB: `{p.get('avg_severity')}`)\n  * {p.get('description')}\n"

    md += """
---

## 🛠️ Khuyến nghị Hành động Vận hành Cụ thể

Ban điều hành chuỗi nhà hàng nên tập trung thực hiện các hành động sau:

"""
    for idx, act in enumerate(data.get("recommended_actions", [])):
        md += f"{idx+1}. **{act}**\n"

    md += f"""
---
*Báo cáo được kết xuất tự động từ cơ sở dữ liệu phân tích. Vui lòng tham chiếu chi tiết tại Dashboard chính.*
"""
    return md


def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
        
    parser = argparse.ArgumentParser(description="Generate customer insight reports in Markdown and HTML.")
    parser.add_argument("--period", type=str, default="7d", choices=["7d", "30d"], help="Reporting period (7d or 30d)")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save report files (default: workspace/reports)")
    parser.add_argument("--format", type=str, default="all", choices=["md", "html", "all"], help="Output format")
    args = parser.parse_args()

    # Resolve output directory
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.join(workspace_root, "reports")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load data & verify
    records = tools.load_review_data()
    if not records:
        print("[Warning] No data records found in analyzed_reviews.json. Cannot generate report metrics.")
        print("Please run rule_analyzer.py or analyze.py to create the dataset first.")
        # Create a mock report or exit
        sys.exit(1)

    print(f"[Report] Loaded {len(records)} review aspects. Generating report for period '{args.period}'...")

    # 2. Get metrics
    summary_data = tools.generate_weekly_summary(period=args.period)
    prioritized = tools.prioritize_risks(period=args.period, limit=5)

    # Add extra raw counts for header template
    unique_review_ids = set(r["review_id"] for r in records)
    summary_data["total_reviews"] = len(unique_review_ids)
    summary_data["total_aspects"] = len(records)
    
    # Calculate daily timeline charts
    # Group records by day
    daily_sentiment = {}
    daily_volume = {}
    for r in records:
        r_date_str = r.get("created_at", "").split("T")[0]
        if not r_date_str:
            continue
        daily_sentiment.setdefault(r_date_str, []).append(r.get("sentiment", 0.0))
        daily_volume[r_date_str] = daily_volume.get(r_date_str, 0) + 1

    sorted_days = sorted(daily_sentiment.keys())[-30:] # Last 30 days of data for timeline chart
    timeline_dates = []
    timeline_volumes = []
    timeline_sentiments = []
    for d in sorted_days:
        timeline_dates.append(d)
        timeline_volumes.append(daily_volume[d])
        timeline_sentiments.append(round(sum(daily_sentiment[d]) / len(daily_sentiment[d]), 2))

    # Calculate main categories breakdown
    categories = {}
    for r in records:
        cat = r.get("main_category", "OTHER")
        categories[cat] = categories.get(cat, 0) + 1

    chart_data = {
        "timeline": {
            "dates": timeline_dates,
            "volumes": timeline_volumes,
            "sentiments": timeline_sentiments
        },
        "donut": {
            "labels": list(categories.keys()),
            "values": list(categories.values())
        }
    }

    # Generate files names
    filename_base = f"insight_report_{args.period}_{datetime.now().strftime('%Y%m%d')}"
    
    # Render Markdown report
    if args.format in ["md", "all"]:
        md_content = generate_markdown(summary_data, prioritized)
        md_path = os.path.join(output_dir, f"{filename_base}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[Report] Markdown report generated: {md_path}")

    # Render HTML report
    if args.format in ["html", "all"]:
        # Prepare components for HTML template injection
        worst_b = summary_data.get("worst_branch", {})
        best_b = summary_data.get("best_branch", {})
        
        # Determine sentiment color
        sentiment_val = summary_data.get("avg_sentiment", 0.0)
        sentiment_color = "var(--accent-emerald)"
        if sentiment_val < 0:
            sentiment_color = "var(--accent-rose)"
        elif sentiment_val < 0.2:
            sentiment_color = "var(--accent-amber)"

        # Tables: Complaints
        complaint_rows_html = ""
        for item in summary_data.get("top_risks", []):
            trend_class = "success-text" if item.get("trend_pct", 0) < 0 else "warning-text"
            trend_color = "var(--accent-emerald)" if item.get("trend_pct", 0) < 0 else "var(--accent-rose)"
            trend_sign = "+" if item.get("trend_pct", 0) > 0 else ""
            
            complaint_rows_html += f"""
            <tr>
                <td style="font-weight: 600;">{item.get('subcategory')}</td>
                <td>{item.get('mentions')} <span style="font-size:0.75rem; color:{trend_color}; margin-left:5px;">({trend_sign}{item.get('trend_pct')}%)</span></td>
                <td style="color: var(--accent-rose); font-weight: 700;">{item.get('impact_score')}</td>
                <td style="font-size: 0.8rem; color: var(--text-secondary);">{', '.join(item.get('affected_branches', []))}</td>
            </tr>
            """
        if not complaint_rows_html:
            complaint_rows_html = "<tr><td colspan='4' style='text-align:center;'>Không có khiếu nại.</td></tr>"

        # List: Emerging Issues
        emerging_items_html = ""
        for item in summary_data.get("emerging_issues", []):
            emerging_items_html += f"""
            <div class="emerging-item">
                <div class="emerging-header">
                    <span class="emerging-title">🚨 {item.get('subcategory')}</span>
                    <span class="emerging-growth">+{item.get('growth_rate_pct')}% Tăng trưởng</span>
                </div>
                <div class="emerging-body">
                    Lượt nhắc: <strong>{item.get('current_mentions')}</strong> (tuần trước: {item.get('previous_mentions')}) · Nghiêm trọng TB: {item.get('avg_severity')}/5
                </div>
                <div class="emerging-quote">
                    <strong>Bằng chứng:</strong> "{item.get('evidence')}"
                </div>
            </div>
            """
        if not emerging_items_html:
            emerging_items_html = "<div class='empty-state' style='text-align:center; padding: 20px; color: var(--text-secondary);'>Không có bất thường mới nào.</div>"

        # List: Recommendations
        actions_html = ""
        for idx, act in enumerate(summary_data.get("recommended_actions", [])):
            actions_html += f"""
            <li class="action-item">
                <span class="action-num">{idx+1}</span>
                <span class="action-text">{act}</span>
            </li>
            """
        if not actions_html:
            actions_html = "<li class='action-item'><span class='action-text'>Tiếp tục giám sát đánh giá.</span></li>"

        # Render and Inject
        html_content = HTML_TEMPLATE.format(
            datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            period_label="7 ngày qua" if args.period == "7d" else "30 ngày qua",
            total_aspects=summary_data.get("total_aspects", 0),
            total_reviews=summary_data.get("total_reviews", 0),
            avg_sentiment=sentiment_val,
            sentiment_color=sentiment_color,
            worst_branch=worst_b.get("branch_name", "N/A"),
            worst_score=worst_b.get("risk_score", 0.0),
            best_branch=best_b.get("branch_name", "N/A"),
            best_score=best_b.get("strength_score", 0.0),
            complaint_rows=complaint_rows_html,
            emerging_items=emerging_items_html,
            action_items=actions_html,
            chart_data_json=json.dumps(chart_data)
        )

        html_path = os.path.join(output_dir, f"{filename_base}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[Report] HTML report generated: {html_path}")

    print("\n--- Báo cáo Phân tích Hoàn tất ---")
    print(f"Báo cáo được lưu trữ thành công tại mục: {output_dir}")


if __name__ == "__main__":
    main()
