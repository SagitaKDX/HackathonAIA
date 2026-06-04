#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mock Data Generator — Generates realistic analyzed reviews data for testing and demonstration.
Creates the directory data/processed and saves analyzed_reviews.json.
"""

import os
import json
import random
from datetime import datetime, timedelta

# Output path matching tools.py and server.py
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed"))
DATA_FILE = os.path.join(DATA_DIR, "analyzed_reviews.json")

BRANCHES = [
    {"id": "branch_nguyen_hue", "name": "Nguyễn Huệ"},
    {"id": "branch_times_city", "name": "Times City"},
    {"id": "branch_aeon_mall_ha_dong", "name": "Aeon Mall Hà Đông"},
    {"id": "branch_ly_quoc_su", "name": "Lý Quốc Sư"},
    {"id": "branch_hang_bo", "name": "Hàng Bồ"},
    {"id": "branch_vo_chi_cong", "name": "Võ Chí Công"},
    {"id": "branch_cau_giay", "name": "Cầu Giấy"},
    {"id": "branch_vincom", "name": "Vincom"},
    {"id": "branch_kim_nguu", "name": "Kim Ngưu"},
    {"id": "branch_truong_dinh", "name": "Trương Định"},
    {"id": "branch_giai_phong", "name": "Giải Phóng"},
    {"id": "branch_nguyen_chi_thanh", "name": "Nguyễn Chí Thanh"}
]

SOURCES = ["google_maps", "facebook", "shopeefood", "grabfood", "internal_feedback"]

ASPECTS = [
    # FOOD
    ("FOOD", "FOOD_TASTE", "Món lẩu thái chua cay ngon tuyệt, nước dùng đậm đà vừa miệng.", 0.85, 1.0, 1),
    ("FOOD", "FOOD_TASTE", "Thịt bò hơi dai và ướp nhạt quá, không ngon như trước.", 0.90, -0.5, 2),
    ("FOOD", "FOOD_FRESHNESS", "Rau thơm bị héo úa và dính đất cát, cảm giác không được tươi sạch.", 0.88, -0.5, 3),
    ("FOOD", "FOOD_FRESHNESS", "Thịt gà có mùi lạ, ăn vào thấy đau bụng đi ngoài nghi bị ngộ độc thực phẩm.", 0.95, -1.0, 5),
    ("FOOD", "FOOD_TEMPERATURE", "Khoai tây chiên mang ra bị nguội ngắt và ỉu xìu.", 0.82, -0.5, 2),
    ("FOOD", "FOOD_PORTION", "Khẩu phần đĩa ếch xào lèo tèo được vài miếng, quá ít.", 0.80, -0.5, 2),
    
    # SERVICE
    ("SERVICE", "SERVICE_WAIT_TIME", "Phải đợi hơn 45 phút mới lên được món đầu tiên, quá lâu và trễ.", 0.92, -0.5, 3),
    ("SERVICE", "SERVICE_WAIT_TIME", "Chờ đợi mỏi mòn hơn 1 tiếng đồng hồ mà nhân viên báo quên đặt order.", 0.96, -1.0, 4),
    ("SERVICE", "SERVICE_STAFF_ATTITUDE", "Bạn nhân viên phục vụ bàn số 5 rất nhiệt tình, niềm nở chào khách vui vẻ.", 0.94, 1.0, 1),
    ("SERVICE", "SERVICE_STAFF_ATTITUDE", "Thái độ nhân viên thu ngân gắt gỏng, trợn mắt khó chịu khi khách hỏi hóa đơn.", 0.90, -1.0, 4),
    ("SERVICE", "SERVICE_ACCURACY", "Mang nhầm món lẩu riêu cua thành lẩu ếch, làm sai order của nhóm.", 0.85, -0.5, 2),
    ("SERVICE", "SERVICE_RESPONSIVENESS", "Gọi nhân viên xin thêm chén nước mắm mà lờ đi, nhắc 3 lần mới mang ra.", 0.87, -0.5, 2),
    
    # AMBIENCE
    ("AMBIENCE", "AMBIENCE_CLEANLINESS", "Sàn nhà dơ bẩn đầy dầu mỡ trơn trượt, bàn ăn chưa lau kỹ còn dính vết thức ăn cũ.", 0.91, -0.5, 3),
    ("AMBIENCE", "AMBIENCE_CLEANLINESS", "Phát hiện có dị vật bẩn giống như miếng Urgo đã qua sử dụng trong bát súp.", 0.98, -1.0, 5),
    ("AMBIENCE", "AMBIENCE_NOISE", "Không gian quán ồn ào như cái chợ, tiếng nhạc kéo ghế rất nhức đầu.", 0.80, -0.5, 2),
    ("AMBIENCE", "AMBIENCE_COMFORT", "Điều hòa bị hỏng hay sao mà nóng và bí bách quá, mồ hôi nhễ nhại.", 0.84, -0.5, 2),
    ("AMBIENCE", "AMBIENCE_DECOR", "Không gian quán trang trí decor rất xinh, view đẹp mắt thích hợp chụp ảnh.", 0.92, 1.0, 1),
    
    # PRICE
    ("PRICE", "PRICE_VALUE_FOR_MONEY", "Giá cả hơi đắt so với chất lượng đồ ăn và dịch vụ.", 0.86, -0.5, 2),
    ("PRICE", "PRICE_VALUE_FOR_MONEY", "Đồ ăn ngon chất lượng, giá hợp lý rất đáng đồng tiền.", 0.89, 1.0, 1),
    ("PRICE", "PRICE_PROMOTION", "Áp mã giảm giá voucher shopeefood được giảm 50k rất hời.", 0.88, 0.5, 1),
    ("PRICE", "PRICE_HIDDEN_COST", "Nhà hàng thu phụ thu tiền gửi xe 10k không rõ ràng, không hài lòng.", 0.85, -0.5, 2)
]

def generate_mock_records(num_reviews=200):
    records = []
    base_date = datetime(2026, 6, 4, 12, 0, 0)
    
    for i in range(num_reviews):
        # Select branch
        branch = random.choice(BRANCHES)
        source = random.choice(SOURCES)
        
        # Jitter timestamp over last 15 days
        days_offset = random.uniform(0, 15)
        created_at = base_date - timedelta(days=days_offset)
        # Random hour/min
        created_at = created_at.replace(
            hour=random.randint(9, 22),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        # Decide if this review will have 1 or 2 aspects (multi-aspect reviews)
        num_aspects = random.choices([1, 2], weights=[0.8, 0.2])[0]
        review_id = f"rev_{i+1:05d}"
        
        # Randomly choose aspects
        chosen_aspects = random.sample(ASPECTS, num_aspects)
        
        for idx, (cat, sub, content_sample, conf_base, sent_base, sev_base) in enumerate(chosen_aspects):
            # Jitter ratings and sentiments slightly
            sentiment = sent_base
            severity = sev_base
            confidence = round(conf_base + random.uniform(-0.05, 0.05), 2)
            
            # Form rating based on sentiment
            if sentiment >= 0.5:
                rating = 1
            else:
                rating = 0
                
            records.append({
                "review_id": review_id,
                "branch_id": branch["id"],
                "branch_name": branch["name"],
                "source": source,
                "sentiment": sentiment,
                "main_category": cat,
                "subcategory": sub,
                "severity": severity,
                "confidence": confidence,
                "evidence": content_sample,
                "content": content_sample,
                "created_at": created_at.strftime("%Y-%m-%dT%H:%M:%S+07:00"),
                "rating": rating
            })
            
    # Sort by created_at ascending
    records.sort(key=lambda x: x["created_at"])
    return records

def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
        
    print(f"Creating directory {DATA_DIR}...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print(f"Generating mock analyzed reviews...")
    records = generate_mock_records(250)
    
    print(f"Saving {len(records)} aspect records to {DATA_FILE}...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        
    print("\n--- Mock Data Generation Complete ---")
    print("Dữ liệu mẫu đã sẵn sàng! Bây giờ bạn có thể chạy: python src/report_generator.py")

if __name__ == "__main__":
    main()
