# Customer Review Insight Agent - CRM Operational Dashboard

Hệ thống Operational Agent & Dashboard phân tích đánh giá khách hàng thông minh dành cho chuỗi nhà hàng. Dự án chuyển hóa hàng ngàn review thô từ nhiều kênh (Google Maps, ShopeeFood, Facebook, GrabFood, phản hồi nội bộ) thành các hành động vận hành chi tiết dựa trên chỉ số rủi ro (Risk Score) và xu hướng mới nổi (Emerging Issues).

---

## 👥 Thành viên nhóm & Phân công công việc

| MSSV | Họ và Tên | Vai trò & Phân công công việc |
| :--- | :--- | :--- |
| **2A202600872** | **Lê Thanh Minh** | **Nhóm trưởng**: Thiết kế hệ thống, Lập trình Backend (server.py), Phát triển giao diện Dashboard (Frontend UI), Xây dựng các Tools phân tích và logic Agent (Tool-Calling, dynamic tab loader). |
| **2A202600904** | **Nguyễn Văn Minh** | Hỗ trợ chuẩn bị dữ liệu mẫu (mock data) và thiết kế slide thuyết trình demo. |
| **2A202600636** | **Nguyễn Lê Thanh Điệp** | Hỗ trợ chuẩn bị và tìm kiếm dữ liệu; Tinh chỉnh Prompt cho AI Agent. |
| **2A202600585** | **Đỗ Minh Phúc** | Hỗ trợ chuẩn bị và tìm kiếm dữ liệu; Chỉnh sửa và tối ưu cấu hình sử dụng nhà cung cấp OpenAI (OpenAI provider). |
| **2A202600826** | **Phí Đình Mạnh** | Hỗ trợ chuẩn bị tài liệu dự án, thuyết trình và tài liệu hóa hệ thống (Documentation). |

---

## 📂 Cấu trúc Thư mục Dự án

```text
HackathonAIA/
├── data/                       # Dữ liệu dự án (Raw & Processed)
│   ├── raw/                    # Chứa data_spa.csv thô
│   └── processed/              # Dữ liệu sau khi làm sạch và phân tích khía cạnh
├── logs/                       # Nhật ký phân tích và hoạt động
├── reports/                    # Thư mục lưu trữ báo cáo Markdown & HTML được xuất tự động
├── src/                        # Mã nguồn ứng dụng
│   ├── review_crawler/         # Tool cào dữ liệu đánh giá từ ShopeeFood/Foody
│   ├── static/                 # Giao diện tĩnh của Dashboard & AI Chat (HTML, CSS, JS)
│   ├── analyze.py              # Phân tích đánh giá bằng LLM (Gemini API + Key rotation)
│   ├── chat_handler.py         # AI Agent xử lý chat và gọi tool phân tích (Ollama / Qwen)
│   ├── generate_mock_data.py   # Script sinh dữ liệu giả lập cho mục đích thử nghiệm
│   ├── preprocess.py           # Tiền xử lý, chuẩn hóa từ lóng tiếng Việt và biểu tượng cảm xúc
│   ├── report_generator.py     # Xuất báo cáo vận hành tự động (Markdown & HTML kèm biểu đồ)
│   ├── rule_analyzer.py        # Phân tích khía cạnh bằng bộ luật từ khóa (Keyword Taxonomy)
│   ├── server.py               # HTTP Server chạy Dashboard & API Chat Proxy
│   └── tools.py                # Định nghĩa các tool phân tích phục vụ cho AI Agent
├── spec/spec.md                # Tài liệu đặc tả sản phẩm và thiết kế hệ thống (SPEC)
├── requirements.txt            # Danh sách thư viện Python cần thiết
└── README.md                   # Tài liệu hướng dẫn sử dụng (tệp này)
```

---

## 🛠️ Yêu cầu Cài đặt & Khởi động nhanh

### 1. Cài đặt Thư viện Phụ thuộc
Đảm bảo bạn đã cài đặt Python 3.10+ trở lên. Khởi chạy terminal và chạy lệnh:
```bash
pip install -r requirements.txt
```

### 2. Cài đặt Cấu hình API Key (Nếu chạy Phân tích LLM)
* Tạo tệp `apikey.txt` trong thư mục gốc của dự án.
* Điền mã API Key Gemini của bạn vào đó (hỗ trợ nhiều khóa dòng-bằng-dòng để tự động xoay vòng tránh giới hạn băng thông):
  ```text
  YOUR_GEMINI_API_KEY_1
  YOUR_GEMINI_API_KEY_2
  ```

---

## 🔄 Quy trình Chạy Toàn bộ Pipeline

Hệ thống có thể chạy bằng dữ liệu thật (qua Crawler) hoặc chạy thử nghiệm ngay lập tức bằng Dữ liệu Giả lập.

### Bước 1: Thu thập hoặc Khởi tạo Dữ liệu

#### Phương án A: Khởi tạo dữ liệu mẫu (Khuyên dùng để Test nhanh)
```bash
python src/generate_mock_data.py
```
*Lệnh này tự động tạo cơ sở dữ liệu giả lập `data/processed/analyzed_reviews.json` để bạn thử nghiệm Dashboard và Trích xuất báo cáo ngay lập tức.*

#### Phương án B: Thu thập dữ liệu từ ShopeeFood/Foody thật
```bash
python src/review_crawler/crawl_shop_reviews.py --shop "bun bo dat thanh" --limit 50
```

### Bước 2: Tiền xử lý dữ liệu thô (Nếu chạy từ dữ liệu thô ở `data/raw/data_spa.csv`)
Làm sạch, loại bỏ trùng lặp, chuẩn hóa emoji tiếng Việt và phân phối chi nhánh:
```bash
python src/preprocess.py
```

### Bước 3: Phân tích Khía cạnh (Aspect Extraction & Sentiment Scoring)

#### Cách 1: Phân tích nhanh bằng Luật Từ khóa (Rule-based)
```bash
python src/rule_analyzer.py
```

#### Cách 2: Phân tích thông minh bằng LLM (Gemini API)
```bash
python src/analyze.py --batch-size 10
```

### Bước 4: Tạo Báo cáo Vận hành Tự động (Markdown & HTML)
Kết xuất trực tiếp các chỉ số phân tích thành báo cáo gửi Ban Giám đốc:
```bash
python src/report_generator.py --period 7d
```
Báo cáo sẽ được lưu trong thư mục `reports/`. Bạn có thể mở trực tiếp tệp `.html` để xem biểu đồ tương tác.

---

## 🖥️ Khởi động Web Dashboard & AI Chat Agent

Để khởi chạy giao diện điều hành tương tác và Chatbot AI giải đáp dữ liệu:

1. **Khởi chạy máy chủ nội bộ:**
   ```bash
   python src/server.py
   ```
2. **Truy cập Trình duyệt:**
   Mở [http://localhost:8000](http://localhost:8000)

### Tính năng của Dashboard:
* **KPI Operational Board:** Hiển thị tổng số review, điểm sentiment trung bình, nhận diện chi nhánh tệ nhất (Risk) và tốt nhất (Strength).
* **Xu hướng thời gian:** Biểu đồ kết hợp cột và đường hiển thị thể tích phản hồi & biến động sentiment trong 30 ngày.
* **Top Khiếu nại Nghiêm trọng:** Bảng xếp hạng các vấn đề cần xử lý gấp dựa trên chỉ số tác động `Impact Score = Tần suất x Mức độ nghiêm trọng x Độ tin cậy`.
* **Vấn đề mới nổi (Emerging Issues):** Cảnh báo tự động các khía cạnh có số phản hồi tiêu cực tăng đột biến (ví dụ: tăng > 50% trong 7 ngày).
* **Bảng chi tiết bộ lọc:** Bộ lọc nâng cao theo chi nhánh, nguồn (Google, Facebook, ShopeeFood...), cảm xúc, và tìm kiếm nội dung gốc.
* **AI Chat Agent:** Cổng trò chuyện tích hợp mô hình ngôn ngữ lớn (mặc định cấu hình Ollama Qwen Local) có khả năng tự động gọi 11 công cụ phân tích trong [tools.py](file:///D:/Work/project/VINAI/HackathonAIA/src/tools.py) để trả lời các câu hỏi vận hành thực tế của chủ chuỗi.

---

## 📊 Khung Đo lường Chỉ số (Scoring Framework)

Hệ thống vận hành theo các công thức quy định tại tài liệu [spec.md](file:///Users/minhlethanh/Documents/AIA/Hackathon/spec/spec.md):

* **Chỉ số Tác động (Impact Score):**
  $$\text{Impact Score} = \text{Lượt nhắc (Mentions)} \times \text{Mức độ Nghiêm trọng Trung bình (Avg Severity)} \times \text{Độ tin cậy (Avg Confidence)}$$
* **Chỉ số Rủi ro Chi nhánh (Risk Score):**
  $$\text{Risk Score} = \sum (\text{Impact Score của các khía cạnh tiêu cực})$$
* **Chỉ số Điểm mạnh Chi nhánh (Strength Score):**
  $$\text{Strength Score} = \text{Lượt khen} \times \text{Điểm Sentiment Dương TB} \times \text{Độ tin cậy TB}$$
* **Quy tắc Phát hiện Vấn đề Mới nổi (Emerging Issue Rule):**
  $$\text{Growth Rate} \ge 50\% \quad \text{và} \quad \text{Lượt phàn nàn tuần này} \ge 5 \quad \text{và} \quad \text{Mức độ nghiêm trọng TB} \ge 2.5$$
