# Báo cáo Phân tích Phản hồi Khách hàng (InsightAgent)

**Thời gian xuất báo cáo:** 2026-06-04 14:48:11  
**Khoảng thời gian phân tích:** 7 ngày qua  
**Dự án:** Customer Review Insight Agent Plan  

---

## 📊 Chỉ số Hiệu năng Vận hành (KPIs)

| Chỉ số | Giá trị | Chi tiết |
| :--- | :---: | :--- |
| **Tổng số khía cạnh (Aspects)** | 299 | Từ dữ liệu reviews đã làm sạch và phân tích |
| **Chỉ số Hài lòng (Sentiment)** | 0.0 | Điểm cảm xúc trung bình (-1.0 đến 1.0) |
| **Chi nhánh rủi ro nhất** | **Times City** | Risk Score: 32.5 |
| **Chi nhánh hài lòng nhất** | **Võ Chí Công** | Strength Score: 5.0 |

---

## ⚠️ Top Khiếu nại Nghiêm trọng Nhất

Dưới đây là các khiếu nại (complaints) có **Impact Score** cao nhất.

| Vấn đề | Tần suất | Trend | Impact Score | Các chi nhánh bị ảnh hưởng nhiều nhất |
| :--- | :---: | :---: | :---: | :--- |
| FOOD_FRESHNESS | 16 | +33% | **55.7** | Nguyễn Huệ, Times City, Võ Chí Công |
| SERVICE_WAIT_TIME | 17 | +55% | **54.5** | Kim Ngưu, Times City, Võ Chí Công |
| AMBIENCE_CLEANLINESS | 10 | -41% | **37.7** | Kim Ngưu, Nguyễn Huệ, Giải Phóng |

---

## 🚨 Vấn đề Bất thường Mới nổi (Emerging Issues)

Các khía cạnh ghi nhận lượt phàn nàn **tăng trưởng đột biến** trong tuần qua:

1. **SERVICE_WAIT_TIME**
   - **Tỷ lệ tăng trưởng:** `+54.5%`
   - **Số lượt:** 17 (so với 11 tuần trước)
   - **Mức độ nghiêm trọng TB:** `3.4/5`
   - **Trích dẫn bằng chứng:** *"Phải đợi hơn 45 phút mới lên được món đầu tiên, quá lâu và trễ."*

---

## 💡 Đề xuất Thứ tự Ưu tiên Xử lý Rủi ro

Dựa trên thuật toán tính điểm ưu tiên Impact Score:

- **[Độ ưu tiên 1] FOOD_FRESHNESS** (Impact Score: `55.7`, Severity TB: `3.9`)
  * Khách hàng phàn nàn nhiều về FOOD_FRESHNESS tại Nguyễn Huệ, Times City, Võ Chí Công.
- **[Độ ưu tiên 2] SERVICE_WAIT_TIME** (Impact Score: `54.5`, Severity TB: `3.6`)
  * Khách hàng phàn nàn nhiều về SERVICE_WAIT_TIME tại Kim Ngưu, Times City, Võ Chí Công.
- **[Độ ưu tiên 3] AMBIENCE_CLEANLINESS** (Impact Score: `37.7`, Severity TB: `4.2`)
  * Khách hàng phàn nàn nhiều về AMBIENCE_CLEANLINESS tại Kim Ngưu, Nguyễn Huệ, Giải Phóng.
- **[Độ ưu tiên 4] SERVICE_STAFF_ATTITUDE** (Impact Score: `25.5`, Severity TB: `4.0`)
  * Khách hàng phàn nàn nhiều về SERVICE_STAFF_ATTITUDE tại Giải Phóng, Times City, Nguyễn Chí Thanh.
- **[Độ ưu tiên 5] PRICE_VALUE_FOR_MONEY** (Impact Score: `22.2`, Severity TB: `1.9`)
  * Khách hàng phàn nàn nhiều về PRICE_VALUE_FOR_MONEY tại Kim Ngưu, Nguyễn Huệ, Giải Phóng.

---

## 🛠️ Khuyến nghị Hành động Vận hành Cụ thể

Ban điều hành chuỗi nhà hàng nên tập trung thực hiện các hành động sau:

1. **Kiểm tra nguồn cung ứng nguyên liệu tươi và quy trình bảo quản tại chi nhánh Nguyễn Huệ, Times City, Võ Chí Công.**
2. **Tăng cường nhân sự vào giờ cao điểm tại chi nhánh Kim Ngưu, Times City, Võ Chí Công.**
3. **Thực hiện tổng vệ sinh toàn bộ cửa hàng và chấn chỉnh tác phong dọn dẹp tại chi nhánh Kim Ngưu, Nguyễn Huệ, Giải Phóng.**

---
*Báo cáo được kết xuất tự động từ cơ sở dữ liệu phân tích. Vui lòng tham chiếu chi tiết tại Dashboard chính.*
