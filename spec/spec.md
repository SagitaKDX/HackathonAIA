# Customer Review Insight Agent - PRODUCT SPECIFICATION (SPEC)

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

## 1. Bằng chứng về "Nỗi đau" (User Evidence)

### 1.1 Trải nghiệm trực tiếp
Khi tự mình vận hành và quản lý phản hồi khách hàng thông qua các giao diện quản trị truyền thống (như Google Business Profile console, ShopeeFood Merchant App):
- **Bẫy điểm sao (Rating Trap)**: Nhiều khách hàng đánh giá 4/5 sao (vẫn là điểm tốt) nhưng nội dung text lại chứa phàn nàn nghiêm trọng về vệ sinh hoặc thái độ nhân viên phục vụ. Nếu quản lý chỉ nhìn điểm sao trung bình hàng ngày (ví dụ: 4.2/5), họ sẽ hoàn toàn bỏ qua các rủi ro vận hành này cho đến khi khách hàng âm thầm rời bỏ chuỗi.
- **Quá tải thông tin đa kênh**: Review đổ về rải rác từ Google Maps, ShopeeFood, GrabFood, Facebook... Quản lý phải mở từng ứng dụng, sao chép dữ liệu ra Excel để tính toán thủ công, mất trung bình **12 giờ/tuần/chi nhánh** chỉ cho việc phân loại và làm báo cáo.

### 1.2 Bằng chứng từ bên ngoài
- Theo nghiên cứu kinh tế lượng nổi tiếng của *Michael Luca (Harvard Business Review, 2016)*, mỗi 1 sao tăng thêm trên Yelp giúp nhà hàng độc lập tăng 5-9% doanh thu. Tuy nhiên, để tăng sao bền vững, nhà quản lý phải giải quyết triệt để các lỗi vận hành được mô tả trong phần chữ (text reviews) chứ không phải điểm số tổng hợp.
- Khảo sát người tiêu dùng của *BrightLocal (2024)* chỉ ra **78% khách hàng** sẽ không quay lại nhà hàng nếu họ gặp phải một trải nghiệm tồi tệ về phục vụ hoặc vệ sinh mà không được xử lý nhanh chóng.
- Phỏng vấn nhanh với một chủ quản lý chuỗi 3 cửa hàng bún bò tại Hà Nội: *"Tôi không có thời gian đọc hết 500 review mỗi tuần trên Grab và ShopeeFood. Nhiều khi có khách chê đồ ăn có dị vật hoặc nhân viên gửi xe thái độ lồi lõm, tận 1 tuần sau tôi mới biết khi doanh thu chi nhánh đó tụt dốc."*

---

## 2. Lát cắt để Build (Slice to Build)

Nhóm chọn ra lát cắt nhỏ nhất đủ để chứng minh ý tưởng cốt lõi của sản phẩm:

> **Một chủ chuỗi nhà hàng (User)**, thông qua **Dashboard vận hành tích hợp AI Chat (Job)**, có thể phát hiện ngay **chi nhánh có rủi ro vận hành cao nhất trong tuần kèm bằng chứng trích dẫn cụ thể (Decision/Insight)** và **đưa ra hành động cải thiện chính xác nhất (Result)**.

Lát cắt này được hiện thực hóa bằng:
1. Giao diện Dashboard hiển thị **Risk Score** và các khía cạnh tiêu cực nổi trội của từng chi nhánh.
2. Trợ lý AI Copilot có khả năng tự động gọi các công cụ truy xuất review thô (`get_supporting_quotes`, `get_reviews`) để cung cấp bằng chứng trực tiếp cho người dùng.

---

## 3. AI Product Canvas

| Ô | Câu hỏi cần trả lời | Giải pháp chi tiết của InsightAgent |
| :--- | :--- | :--- |
| **Value (Giá trị)** | Sản phẩm dành cho ai? Họ đau ở đâu? AI giải quyết điều gì tốt hơn cách làm cũ? | - **Đối tượng**: Chủ chuỗi và quản lý vận hành F&B.<br>- **Nỗi đau**: Mất thời gian tổng hợp thủ công, bỏ sót sự cố nghiêm trọng do bẫy điểm sao.<br>- **AI giải quyết**: Tự động phân tách khía cạnh (ABSA) và chấm điểm Sentiment/Severity chính xác. Tổng hợp thành các chỉ số định lượng trực quan (Risk Score, Emerging Issues) để quản lý biết chính xác cần sửa lỗi gì ngay lập tức. |
| **Trust (Niềm tin)** | Khi AI trả lời sai, người dùng nhận ra bằng cách nào? Họ sửa lại, hoàn tác hay chuyển sang người thật ra sao? | - **Cách nhận biết**: Dưới mỗi phân tích hoặc cảnh báo rủi ro, hệ thống luôn đính kèm **bằng chứng thô (evidence/quote)** trích từ review gốc của khách hàng để người dùng tự đối chiếu.<br>- **Cách xử lý**: Nếu AI phân loại nhầm khía cạnh, người dùng có thể sử dụng bộ lọc thủ công trên Dashboard hoặc gõ yêu cầu vào AI Chat để truy vấn trực tiếp review gốc qua công cụ tìm kiếm từ khóa (`search_reviews`). |
| **Feasibility (Tính khả thi)** | Có đáng để build không? (Chi phí, độ trễ, dữ liệu, rủi ro lớn nhất, ngưỡng dừng lại) | - **Độ trễ**: Dưới 3 giây nhờ cơ chế lưu dữ liệu aggregate tại tầng trung gian.<br>- **Chi phí**: Tối ưu hóa bằng cách chạy phân tích ABSA một lần khi dữ liệu mới đổ về và lưu lại. Chatbot chỉ truy vấn dữ liệu đã tính toán.<br>- **Dữ liệu**: Dữ liệu thô cào từ Google Maps/ShopeeFood/GrabFood và tập dữ liệu feedback nội bộ.<br>- **Rủi ro lớn nhất**: Mô hình LLM bị ảo giác (hallucination) bịa số liệu.<br>- **Ngưỡng dừng**: Hệ thống chặn hoàn toàn các câu hỏi ngoài phạm vi F&B và chặn Prompt Injection. |
| **Tín hiệu học** | Khi người dùng chỉnh sửa kết quả, dữ liệu đó đi về đâu và giúp sản phẩm khá lên nhờ tín hiệu nào? | - Lịch sử lọc dữ liệu, từ khóa tìm kiếm và các phản hồi sai lệch của người dùng được ghi nhận vào nhật ký hệ thống (`logs/`).<br>- Dữ liệu này được sử dụng làm tập dữ liệu kiểm thử (Evaluation Dataset) để liên tục tinh chỉnh Prompt của LLM và cập nhật từ điển tiền xử lý từ lóng tiếng Việt (`preprocess.py`). |

---

## 4. Tăng năng lực (Augmentation) hay Tự động hóa (Automation)

**InsightAgent được thiết kế theo hướng Tăng năng lực (Augmentation - Con người giữ quyền quyết định cuối cùng).**

- **Phạm vi hoạt động của AI**: Tự động hóa hoàn toàn các khía cạnh kỹ thuật phức tạp như thu thập, làm sạch tiếng Việt (loại bỏ slang, chuẩn hóa emoji), trích xuất khía cạnh (ABSA), tính toán các chỉ số rủi ro (Risk/Strength Score) và tổng hợp báo cáo.
- **Quy trình quyết định của con người**: Chủ chuỗi/Quản lý giữ toàn quyền đưa ra các quyết định hành động thực tế (ví dụ: kỷ luật nhân viên, thay đổi nhà cung cấp thực phẩm, cấu hình lại menu).
- **Lý do lựa chọn**: Sai sót trong quyết định vận hành nhà hàng có thể ảnh hưởng lớn đến nhân sự hoặc pháp lý (ví dụ: sa thải nhân viên dựa trên đánh giá sai của AI). Do đó, AI chỉ đóng vai trò chuẩn bị báo cáo vận hành, cung cấp bằng chứng và đề xuất ưu tiên hành động để con người duyệt và thực thi. Hậu quả của sai sót phân loại được giảm thiểu tối đa nhờ việc luôn hiển thị bằng chứng thô để con người kiểm chứng trước khi ra quyết định.

---

## 5. Bốn đường đi của trải nghiệm (4 Experience Paths)

| Đường đi | Tình huống | Cách xử lý trong thiết kế của InsightAgent |
| :--- | :--- | :--- |
| **Đường thuận (Happy Path)** | AI đúng và tự tin | - Giao diện hiển thị trực quan các thẻ cảnh báo rủi ro (Risk Cards) kèm theo tags khía cạnh rõ ràng.<br>- Nút bấm **Xem trích dẫn** hiện ngay bên cạnh để người dùng kiểm chứng nhanh trong 1 click. |
| **Khi AI không chắc** | AI lưỡng lự (Confidence thấp) | - Trong AI Chat, chatbot sẽ trả lời kèm cảnh báo mức độ tin cậy thấp của dữ liệu và đưa ra 2-3 khía cạnh gần nhất để người dùng lựa chọn.<br>- Hệ thống tự động gán nhãn `OTHER` trên Dashboard nếu độ tin cậy dưới 60%. |
| **Khi AI sai** | Kết quả phân loại sai lệch | - Trích dẫn gốc (evidence) hiển thị ngay dưới phân tích giúp người dùng lập tức phát hiện sự sai lệch.<br>- Người dùng có thể sử dụng ô **Tìm kiếm bằng chứng** thủ công hoặc bộ lọc chi nhánh/nguồn để lọc lại dữ liệu chính xác. |
| **Khi người dùng sửa** | Người dùng chỉnh lại bộ lọc | - Ghi nhận lại thao tác điều chỉnh bộ lọc hoặc từ khóa tìm kiếm của người dùng vào log file để làm cơ sở cập nhật bộ luật Keyword Taxonomy trong tương lai. |

---

## 6. Những kiểu lỗi đáng lo nhất (Worst Failure Modes)

### 6.1 Lỗi phân loại nhầm sự cố nghiêm trọng (Critical Misclassification)
- **Mô tả**: Khách phàn nàn về ngộ độc thực phẩm hoặc dị vật nguy hiểm (Severity 5 - Critical) nhưng AI phân tích nhầm thành phàn nàn chất lượng món ăn thông thường (Severity 1 - Minor) do ngôn từ mỉa mai của khách hàng.
- **Hậu quả**: Ban quản trị bỏ sót sự cố nghiêm trọng, dẫn đến nguy cơ khủng hoảng truyền thông hoặc bị cơ quan chức năng kiểm tra vệ sinh ATTP.
- **Giải pháp xử lý**: Thiết lập bộ luật cứng (Rule-based) quét song song trong `rule_analyzer.py` và `preprocess.py`. Nếu phát hiện các từ khóa nhạy cảm cực đoan (như "ngộ độc", "nhập viện", "dị vật", "gián", "chuột", "đau bụng"), hệ thống bắt buộc ghi đè (override) gán mức độ nghiêm trọng `Severity = 5 (Critical)` và gửi cảnh báo ngay lập tức lên bảng Emerging Issues.

### 6.2 Lỗi ảo giác dữ liệu chatbot (AI Agent Hallucination)
- **Mô tả**: AI Chat tự bịa ra số liệu thống kê hoặc trích dẫn không có thật khi người dùng hỏi các câu hỏi vĩ mô hoặc ngoài dải dữ liệu.
- **Hậu quả**: Ban quản trị đưa ra quyết định sai lầm dựa trên số liệu giả mạo.
- **Giải pháp xử lý**:
  - Áp dụng kỹ thuật **RAG nghiêm ngặt (Retrieval-Augmented Generation)**: Trong System Prompt, cấm tuyệt đối LLM tự trả lời nếu không gọi tools lấy dữ liệu thực tế.
  - Mỗi câu trả lời thống kê bắt buộc hiển thị tên công cụ đã gọi (ví dụ: `prioritize_risks()`) để người dùng kiểm chứng tính minh bạch.

---

## 7. Kế hoạch kiểm thử và bằng chứng demo

### 7.1 Đầu vào kiểm thử (Test Inputs)

1. **Đầu vào bình thường (Đường thuận)**:
   - *Review thô*: "Món lẩu thái hôm nay nguội lạnh, lại bắt tôi đợi tận 45 phút mới mang ra."
   - *Kết quả mong đợi*: Hệ thống trích xuất ra 2 khía cạnh:
     - `FOOD_TEMPERATURE`: Sentiment = -1.0 (Tiêu cực), Severity = 2 (Low), Evidence = "lẩu thái hôm nay nguội lạnh".
     - `SERVICE_WAIT_TIME`: Sentiment = -1.0 (Tiêu cực), Severity = 4 (High), Evidence = "đợi tận 45 phút".

2. **Đầu vào khó/nhiễu (Mỉa mai & Ẩn dụ)**:
   - *Review thô*: "Bún đậu ở đây vệ sinh sạch sẽ đến mức ăn xong cả nhà tôi phải vào bệnh viện truyền nước gấp!"
   - *Kết quả mong đợi*: Dù có từ "sạch sẽ", hệ thống vẫn phải phát hiện từ khóa "bệnh viện", "truyền nước" để gán nhãn:
     - `FOOD_FRESHNESS`: Sentiment = -1.0 (Tiêu cực), Severity = 5 (Critical), Evidence = "vào bệnh viện truyền nước gấp".

### 7.2 Bằng chứng Demo (Demo Artifacts)
- **Kiến trúc mã nguồn**: File [server.py](file:///Users/minhlethanh/Documents/AIA/Hackathon/src/server.py) và [chat_handler.py](file:///Users/minhlethanh/Documents/AIA/Hackathon/src/chat_handler.py) thiết lập cơ chế Tool-Calling bảo mật, chống prompt injection.
- **Bảng dữ liệu đã phân tích**: [analyzed_reviews.json](file:///Users/minhlethanh/Documents/AIA/Hackathon/data/processed/analyzed_reviews.json) hiển thị đầy đủ cấu trúc dữ liệu khía cạnh (Aspect-level).
- **Giao diện Dashboard**: Tích hợp tab [Giới thiệu](file:///Users/minhlethanh/Documents/AIA/Hackathon/src/static/intro.html) trực quan hóa toàn bộ triết lý sản phẩm.

---

## 8. Khung phân tích kỹ thuật (Technical Specifications)

*(Được kế thừa và đồng bộ từ kiến trúc kỹ thuật của hệ thống)*

### 8.1 DINESERV Quality Dimensions Mapping
Hệ thống ánh xạ 19 Aspect Labels sang 5 chiều kích chất lượng dịch vụ của mô hình DINESERV (Stevens et al. 1995):
1. **Hữu hình (Tangibles)**: `AMBIENCE_CLEANLINESS`, `AMBIENCE_NOISE`, `AMBIENCE_COMFORT`, `AMBIENCE_DECOR`, `AMBIENCE_SEATING`
2. **Tin cậy (Reliability)**: `FOOD_TASTE`, `FOOD_FRESHNESS`, `FOOD_TEMPERATURE`, `FOOD_PORTION`, `FOOD_PRESENTATION`, `FOOD_QUALITY`
3. **Phản hồi (Responsiveness)**: `SERVICE_WAIT_TIME`, `SERVICE_RESPONSIVENESS`
4. **Đảm bảo (Assurance)**: `PRICE_VALUE_FOR_MONEY`, `PRICE_HIDDEN_COST`, `SERVICE_ACCURACY`
5. **Thấu cảm (Empathy)**: `SERVICE_STAFF_ATTITUDE`, `PRICE_PROMOTION`, `SERVICE_PROFESSIONALISM`

### 8.2 Tool API Specifications
Hệ thống tích hợp bộ 12 công cụ phân tích tự động (Retrieval, Analytics, và Executive) như đã định nghĩa chi tiết tại file mã nguồn [tools.py](file:///Users/minhlethanh/Documents/AIA/Hackathon/src/tools.py) phục vụ cho cơ chế Function Calling của AI Agent.
