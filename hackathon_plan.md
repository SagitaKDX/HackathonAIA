# Customer Review Insight Agent Plan

## 0. Mục tiêu sản phẩm

Hệ thống không chỉ "phân loại review". Mục tiêu chính là biến hàng nghìn review từ nhiều kênh thành insight vận hành để chủ chuỗi nhà hàng biết:

- Chi nhánh nào đang có rủi ro cao.
- Khách đang phàn nàn điều gì nhiều nhất.
- Điểm mạnh nào nên tiếp tục phát huy.
- Vấn đề mới nào đang tăng bất thường.
- Nếu chỉ xử lý 1 việc trong tuần này thì nên xử lý việc nào.

Người dùng chính: chủ chuỗi nhà hàng, quản lý vùng, quản lý chi nhánh, team CSKH.

---

## 1. Nguyên tắc cho LLM Agent

LLM nên hành động theo các nguyên tắc sau:

1. Không đọc tất cả review nếu câu hỏi là câu hỏi tổng hợp.
2. Ưu tiên gọi analytics tool đã aggregate sẵn.
3. Chỉ lấy review gốc khi cần bằng chứng, quote hoặc kiểm tra một vấn đề cụ thể.
4. Mỗi câu trả lời nên có số liệu, xu hướng, chi nhánh liên quan và bằng chứng ngắn.
5. Nếu thiếu thời gian phân tích, mặc định dùng `period="7d"` cho câu hỏi tuần này và `period="30d"` cho câu hỏi tổng quan.
6. Khi đưa khuyến nghị, sắp xếp theo `Impact Score`, không sắp xếp chỉ theo số lượng mention.

---

## 2. Pipeline tổng quát

```text
Review Sources
  -> Data Cleaning
  -> Review Analysis
  -> Aggregation Layer
  -> Insight Layer
  -> Report Generation
```

### 2.1 Review Sources

Nguồn review đầu vào:

- Google Maps
- Facebook
- ShopeeFood
- GrabFood
- Internal Feedback

### 2.2 Data Cleaning

Mục tiêu: làm sạch để review có thể phân tích ổn định.

- Remove spam.
- Remove duplicates.
- Normalize emoji, slang, typo phổ biến.
- Chuẩn hóa ngày giờ, chi nhánh, kênh review.
- Tách review dài thành các ý nếu một review nói nhiều vấn đề.

### 2.3 Review Analysis

Mỗi review sau khi làm sạch cần có các nhãn sau:

- `sentiment`
- `main_category`
- `subcategory`
- `severity`
- `confidence`
- `branch_id`
- `source`
- `created_at`

### 2.4 Aggregation Layer

Dữ liệu được tổng hợp theo:

- Branch
- Time window: day, week, month
- Main category
- Subcategory
- Sentiment
- Severity
- Source

### 2.5 Insight Layer

Insight cần sinh ra:

- Top risks
- Top strengths
- Trend detection
- Emerging issues
- Branch comparison
- Recommended actions

### 2.6 Report Generation

Đầu ra cho người dùng:

- Dashboard
- Markdown report
- Executive summary
- Action recommendations

---

## 3. Data Schema

### 3.1 Raw Review

```json
{
  "review_id": "rev_001",
  "branch_id": "branch_nguyen_hue",
  "branch_name": "Nguyen Hue",
  "source": "google_maps",
  "rating": 2,
  "content": "Doi hon 40 phut, mon mang ra bi nguoi.",
  "created_at": "2026-06-01T19:30:00+07:00"
}
```

### 3.2 Analyzed Review

```json
{
  "review_id": "rev_001",
  "branch_id": "branch_nguyen_hue",
  "sentiment": -1.0,
  "main_category": "SERVICE",
  "subcategory": "SERVICE_WAIT_TIME",
  "severity": 4,
  "confidence": 0.92,
  "evidence": "Doi hon 40 phut",
  "created_at": "2026-06-01T19:30:00+07:00"
}
```

Nếu một review có nhiều vấn đề, tạo nhiều analyzed records cùng `review_id` nhưng khác `subcategory`.

---

## 4. Taxonomy

| Main Category | Subcategory | Mô tả |
| --- | --- | --- |
| FOOD | FOOD_TASTE | Món ngon, dở, nhạt, đậm vị |
|  | FOOD_FRESHNESS | Độ tươi, mùi lạ, thực phẩm cũ |
|  | FOOD_TEMPERATURE | Món nóng, nguội, không đúng nhiệt độ |
|  | FOOD_PORTION | Khẩu phần nhiều, ít, không đều |
|  | FOOD_PRESENTATION | Cách trình bày món |
| SERVICE | SERVICE_WAIT_TIME | Đợi lâu, lên món chậm |
|  | SERVICE_STAFF_ATTITUDE | Thái độ nhân viên |
|  | SERVICE_ACCURACY | Mang nhầm món, thiếu món |
|  | SERVICE_RESPONSIVENESS | Phản hồi chậm, không hỗ trợ |
|  | SERVICE_PROFESSIONALISM | Tác phong, quy trình, xử lý tình huống |
| AMBIENCE | AMBIENCE_CLEANLINESS | Vệ sinh bàn, sàn, toilet, dụng cụ |
|  | AMBIENCE_NOISE | Ồn, âm thanh khó chịu |
|  | AMBIENCE_COMFORT | Sự thoải mái, nhiệt độ phòng, ánh sáng |
|  | AMBIENCE_DECOR | Trang trí, không gian, hình ảnh |
|  | AMBIENCE_SEATING | Chỗ ngồi, bàn ghế, sắp xếp bàn |
| PRICE | PRICE_VALUE_FOR_MONEY | Đáng tiền hay không |
|  | PRICE_PORTION_FAIRNESS | Giá so với khẩu phần |
|  | PRICE_PROMOTION | Voucher, khuyến mãi, mã giảm giá |
|  | PRICE_HIDDEN_COST | Phụ thu, phí không rõ |
| OTHER | OTHER | Không xác định hoặc nằm ngoài taxonomy |

---

## 5. Scoring Framework

### 5.1 Sentiment Score

| Score | Meaning |
| --- | --- |
| -1.0 | Rất tiêu cực |
| -0.5 | Tiêu cực |
| 0 | Trung lập |
| 0.5 | Tích cực |
| 1.0 | Rất tích cực |

### 5.2 Severity Score

| Score | Meaning | Ví dụ |
| --- | --- | --- |
| 1 | Minor | "Món hơi nguội" |
| 2 | Low | "Phục vụ hơi chậm" |
| 3 | Medium | "Đợi 30 phút mới có món" |
| 4 | High | "Đợi hơn 1 giờ" |
| 5 | Critical | "Ngộ độc thực phẩm" |

### 5.3 Impact Score

```text
Impact Score = Mentions x Avg Severity x Avg Confidence
```

Ví dụ:

```text
Mentions = 120
Avg Severity = 4
Avg Confidence = 0.9

Impact Score = 120 x 4 x 0.9 = 432
```

### 5.4 Risk Score

Dùng để xếp hạng chi nhánh có vấn đề.

```text
Risk Score = sum(Impact Score của các subcategory có sentiment < 0)
```

### 5.5 Strength Score

Dùng để tìm điểm mạnh.

```text
Strength Score = Positive Mentions x Avg Positive Sentiment x Avg Confidence
```

### 5.6 Emerging Issue Rule

Một vấn đề được xem là emerging issue nếu:

```text
Current Mentions >= 10
AND Growth Rate >= 100%
AND Avg Severity >= 3
```

```text
Growth Rate = (Current Period Mentions - Previous Period Mentions) / max(Previous Period Mentions, 1)
```

---

## 6. Tool Contract cho Agent

Agent nên dùng 3 tầng tool:

```text
Level 1 - Retrieval
  get_reviews()
  search_reviews()
  get_supporting_quotes()

Level 2 - Analytics
  get_top_complaints()
  get_top_strengths()
  detect_emerging_issues()
  get_category_breakdown()
  rank_branches()

Level 3 - Executive
  prioritize_risks()
  generate_weekly_summary()
```

### 6.1 Retrieval Tools

#### get_reviews

Dùng khi cần lấy review gốc theo filter.

```python
get_reviews(
    branch_id=None,
    start_date=None,
    end_date=None,
    sentiment=None,
    category=None,
    subcategory=None,
    limit=50
)
```

#### search_reviews

Dùng khi user hỏi một từ khóa cụ thể như "nguội", "đợi lâu", "voucher".

```python
search_reviews(
    keyword,
    branch_id=None,
    start_date=None,
    end_date=None,
    limit=50
)
```

#### get_supporting_quotes

Dùng để lấy bằng chứng đại diện cho một issue.

```python
get_supporting_quotes(
    issue_id,
    branch_id=None,
    limit=5
)
```

Trả về:

```json
{
  "issue_id": "SERVICE_WAIT_TIME",
  "quotes": [
    {
      "review_id": "rev_001",
      "branch_name": "Nguyen Hue",
      "quote": "Doi hon 40 phut",
      "confidence": 0.92
    }
  ]
}
```

### 6.2 Analytics Tools

#### get_top_complaints

Dùng khi user hỏi khách hàng đang không hài lòng về điều gì.

```python
get_top_complaints(
    branch_id=None,
    period="7d",
    limit=5
)
```

Trả về:

```json
{
  "period": "7d",
  "items": [
    {
      "subcategory": "SERVICE_WAIT_TIME",
      "mentions": 132,
      "trend_pct": 42,
      "impact_score": 820,
      "affected_branches": ["Nguyen Hue", "Times City"]
    }
  ]
}
```

#### get_top_strengths

Dùng khi user hỏi điểm mạnh, khách thích gì, thương hiệu được khen gì.

```python
get_top_strengths(
    branch_id=None,
    period="30d",
    limit=5
)
```

#### detect_emerging_issues

Dùng khi user hỏi có dấu hiệu bất thường, vấn đề mới, spike hoặc anomaly.

```python
detect_emerging_issues(
    branch_id=None,
    period="7d",
    limit=5
)
```

#### get_category_breakdown

Dùng khi user muốn biết tỷ trọng vấn đề theo FOOD, SERVICE, AMBIENCE, PRICE.

```python
get_category_breakdown(
    branch_id,
    period="30d"
)
```

Trả về:

```json
{
  "branch_id": "branch_nguyen_hue",
  "period": "30d",
  "breakdown": {
    "FOOD": 35,
    "SERVICE": 45,
    "AMBIENCE": 10,
    "PRICE": 10
  }
}
```

#### rank_branches

Dùng khi user muốn so sánh chi nhánh.

```python
rank_branches(
    metric="risk",
    period="7d",
    limit=10
)
```

Metric hỗ trợ:

- `risk`
- `rating`
- `sentiment`
- `complaint_volume`
- `strength`

### 6.3 Executive Tools

#### prioritize_risks

Dùng khi user hỏi nên xử lý gì trước.

```python
prioritize_risks(
    branch_id=None,
    period="7d",
    limit=3
)
```

#### generate_weekly_summary

Dùng khi user cần báo cáo tổng hợp.

```python
generate_weekly_summary(
    period="7d"
)
```

Trả về:

```json
{
  "period": "7d",
  "top_risks": [],
  "top_strengths": [],
  "worst_branch": {},
  "best_branch": {},
  "emerging_issues": [],
  "recommended_actions": []
}
```

---

## 7. Agent Decision Guide

| User intent | Example question | Tool sequence |
| --- | --- | --- |
| Tìm chi nhánh tệ nhất | "Chi nhánh nào đang có vấn đề nhất?" | `rank_branches(metric="risk")` -> `get_supporting_quotes()` |
| Tìm complaint lớn nhất | "Khách phàn nàn gì nhiều nhất?" | `get_top_complaints()` -> `get_supporting_quotes()` |
| Tìm điểm mạnh | "Khách thích điều gì nhất?" | `get_top_strengths()` -> `get_supporting_quotes()` |
| Tìm vấn đề mới | "Có dấu hiệu bất thường không?" | `detect_emerging_issues()` -> `get_supporting_quotes()` |
| So sánh chi nhánh | "So sánh chất lượng các chi nhánh" | `rank_branches()` -> `get_category_breakdown()` |
| Ưu tiên hành động | "Nếu chỉ sửa 1 việc thì sửa gì?" | `prioritize_risks()` -> `get_supporting_quotes()` |
| Tìm review theo keyword | "Tìm review nói món nguội" | `search_reviews(keyword="mon nguoi")` |
| Báo cáo tuần | "Tóm tắt tình hình tuần này" | `generate_weekly_summary()` |

---

## 8. Key Use Cases

### Use Case 1: Chi nhánh nào đang có vấn đề nhất?

User hỏi:

```text
Chi nhánh nào có chất lượng giảm mạnh nhất tuần này?
```

Tool sequence:

```text
rank_branches(metric="risk", period="7d")
get_supporting_quotes(issue_id=<top_issue>, branch_id=<worst_branch>)
```

Output mẫu:

```text
Chi nhánh cần chú ý nhất là Nguyễn Huệ.

Risk Score: 820 (+42% so với tuần trước)

Nguyên nhân chính:
1. SERVICE_WAIT_TIME: 132 mentions
2. FOOD_TEMPERATURE: 85 mentions

Bằng chứng:
- "Đợi hơn 40 phút"
- "Món ăn bị nguội"

Khuyến nghị:
Tăng nhân sự giờ cao điểm và kiểm tra quy trình giữ nhiệt món trước khi giao bàn.
```

### Use Case 2: Khách hàng đang phàn nàn điều gì nhiều nhất?

User hỏi:

```text
Khách hàng đang không hài lòng nhất về điều gì?
```

Tool sequence:

```text
get_top_complaints(period="7d")
get_supporting_quotes(issue_id=<top_complaint>)
```

Output mẫu:

```text
Vấn đề lớn nhất hiện tại là SERVICE_WAIT_TIME.

Top complaints:
1. SERVICE_WAIT_TIME: 132 mentions, Impact Score 820
2. FOOD_TEMPERATURE: 85 mentions, Impact Score 510
3. PRICE_VALUE_FOR_MONEY: 60 mentions, Impact Score 360

Nhận định:
Vấn đề thời gian chờ đang ảnh hưởng nhiều chi nhánh, đặc biệt là Nguyễn Huệ và Times City.
```

### Use Case 3: Điểm mạnh lớn nhất của thương hiệu là gì?

User hỏi:

```text
Khách hàng thích điều gì nhất?
```

Tool sequence:

```text
get_top_strengths(period="30d")
```

Output mẫu:

```text
Điểm mạnh lớn nhất là FOOD_TASTE.

Top strengths:
1. FOOD_TASTE: 350 positive mentions
2. SERVICE_STAFF_ATTITUDE: 240 positive mentions
3. AMBIENCE_DECOR: 180 positive mentions

Nhận định:
Thương hiệu đang được khen về hương vị món ăn và trải nghiệm nhân viên.
```

### Use Case 4: Có vấn đề mới nào đang xuất hiện không?

User hỏi:

```text
Có dấu hiệu bất thường nào trong tuần này không?
```

Tool sequence:

```text
detect_emerging_issues(period="7d")
get_supporting_quotes(issue_id=<emerging_issue>)
```

Output mẫu:

```text
Có một vấn đề mới đang tăng nhanh: FOOD_FRESHNESS.

Số liệu:
- Tuần trước: 5 mentions
- Tuần này: 37 mentions
- Growth: +640%
- Avg Severity: 3.8

Bằng chứng:
- "Thịt không còn tươi"
- "Rau có mùi lạ"

Khuyến nghị:
Kiểm tra nguồn hàng và quy trình bảo quản tại các chi nhánh có mention cao.
```

### Use Case 5: So sánh các chi nhánh

User hỏi:

```text
So sánh chất lượng giữa các chi nhánh.
```

Tool sequence:

```text
rank_branches(metric="risk", period="7d")
rank_branches(metric="strength", period="7d")
```

Output mẫu:

```text
Top branches:
1. Vincom
2. Times City
3. Nguyễn Chí Thanh

Lowest branches by risk:
1. Nguyễn Huệ
2. Giải Phóng

Nhận định:
Nguyễn Huệ có risk cao nhất do SERVICE_WAIT_TIME và FOOD_TEMPERATURE. Vincom ổn định hơn nhờ FOOD_TASTE và SERVICE_STAFF_ATTITUDE.
```

### Use Case 6: Cần ưu tiên xử lý gì trước?

User hỏi:

```text
Nếu chỉ sửa 1 vấn đề tuần này thì nên sửa gì?
```

Tool sequence:

```text
prioritize_risks(period="7d", limit=1)
get_supporting_quotes(issue_id=<priority_issue>)
```

Output mẫu:

```text
Ưu tiên số 1: SERVICE_WAIT_TIME.

Impact Score: 920
Affected branches:
- Nguyễn Huệ
- Times City

Lý do:
Vấn đề này có số mention cao, severity trung bình cao và đang tăng so với tuần trước.

Nguyên nhân khả năng cao:
Thiếu nhân sự giờ cao điểm hoặc bếp không đồng bộ với lượng order.

Hành động đề xuất:
Tăng nhân sự khung 18:00-20:00 và theo dõi lại complaint trong 7 ngày tiếp theo.
```

---

## 9. Response Template cho LLM

### 9.1 Template ngắn cho câu hỏi vận hành

```text
Kết luận: <một câu trả lời thẳng vào câu hỏi>

Số liệu chính:
- <metric 1>
- <metric 2>
- <metric 3>

Bằng chứng:
- "<quote 1>"
- "<quote 2>"

Khuyến nghị:
<hành động cụ thể, có ưu tiên>
```

### 9.2 Template báo cáo tuần

```text
Executive Summary

1. Top Risk
<issue>, Impact Score <score>, trend <trend_pct>

2. Top Strength
<issue>, positive mentions <count>

3. Worst Branch
<branch>, Risk Score <score>

4. Best Branch
<branch>, Strength Score <score>

5. Emerging Issue
<issue>, growth <trend_pct>

6. Recommended Actions
- <action 1>
- <action 2>
- <action 3>
```

---

## 10. Implementation Notes

- Lưu analyzed review ở dạng record-level để aggregate linh hoạt.
- Nên có bảng riêng cho `branches`, `raw_reviews`, `analyzed_reviews`, `aggregated_metrics`.
- Nên cache kết quả aggregate theo ngày, tuần, tháng để tool chạy nhanh.
- Dashboard chỉ nên đọc từ aggregation layer, không query trực tiếp hàng nghìn review.
- LLM chỉ nên nhận output tool đã có cấu trúc JSON, sau đó viết câu trả lời tự nhiên cho người dùng.
- Mỗi insight quan trọng nên có `supporting_quotes` để tránh cảm giác AI nói chung chung.

