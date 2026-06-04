import os
import json
import re
import pandas as pd
from tqdm import tqdm

# Paths
INPUT_PATH = "data/processed/cleaned_reviews.json"
OUTPUT_JSON_PATH = "data/processed/analyzed_reviews.json"
OUTPUT_CSV_PATH = "data/processed/analyzed_reviews.csv"

# Keyword dictionary mapping subcategories to key Vietnamese words
KEYWORD_TAXONOMY = {
    "FOOD_TASTE": {
        "main": "FOOD",
        "keywords": ["ngon", "dở", "chán", "mặn", "nhạt", "vừa vị", "vừa miệng", "thơm", "ngấy", "béo", "tanh", "hắc", "ngọt", "chua", "cay", "đắng", "khô", "dai", "hương vị", "bánh ngon", "lẩu ngon", "ếch ngon", "súp ngon"]
    },
    "FOOD_FRESHNESS": {
        "main": "FOOD",
        "keywords": ["tươi", "cũ", "ôi", "thiu", "hỏng", "mùi lạ", "hôi", "sống", "chưa chín", "nhiễm khuẩn", "đường ruột", "dạ dày"]
    },
    "FOOD_TEMPERATURE": {
        "main": "FOOD",
        "keywords": ["nóng", "nguội", "lạnh", "đá", "ấm", "giữ nhiệt"]
    },
    "FOOD_PORTION": {
        "main": "FOOD",
        "keywords": ["nhiều", "ít", "đầy đặn", "khẩu phần", "no căng", "lèo tèo", "đĩa to", "đĩa nhỏ", "tô to", "topping", "đầy ự"]
    },
    "FOOD_PRESENTATION": {
        "main": "FOOD",
        "keywords": ["trình bày", "bắt mắt", "đẹp mắt", "nhìn thèm", "hình ảnh minh họa", "bày trí"]
    },
    "SERVICE_WAIT_TIME": {
        "main": "SERVICE",
        "keywords": ["đợi", "chờ", "lâu", "chậm", "nhanh", "trễ", "speed", "giây", "phút", "tiếng", "giờ", "hẹn", "15p", "30p", "40p", "1 tiếng"]
    },
    "SERVICE_STAFF_ATTITUDE": {
        "main": "SERVICE",
        "keywords": ["thái độ", "nhân viên", "pv", "nv", "phục vụ", "nhiệt tình", "vui vẻ", "khó chịu", "niềm nở", "gắt gỏng", "lịch sự", "thân thiện", "đon đả", "chào", "cười", "trợn mắt", "gắt"]
    },
    "SERVICE_ACCURACY": {
        "main": "SERVICE",
        "keywords": ["nhầm", "thiếu", "sai", "lộn", "quên"]
    },
    "SERVICE_RESPONSIVENESS": {
        "main": "SERVICE",
        "keywords": ["phản hồi", "hỗ trợ", "gọi", "yêu cầu", "nhắc", "giục", "lờ đi"]
    },
    "SERVICE_PROFESSIONALISM": {
        "main": "SERVICE",
        "keywords": ["tính tiền", "hóa đơn", "bill", "thanh toán", "thối tiền", "quy trình", "chuyên nghiệp", "nhầm tiền", "máy tính tiền", "order"]
    },
    "AMBIENCE_CLEANLINESS": {
        "main": "AMBIENCE",
        "keywords": ["vệ sinh", "bẩn", "sạch", "tóc", "ruồi", "muỗi", "urgo", "dị vật", "sàn", "bàn", "toilet", "rác", "không gian hẹp", "nhà vệ sinh"]
    },
    "AMBIENCE_NOISE": {
        "main": "AMBIENCE",
        "keywords": ["ồn", "nhạc", "âm thanh", "hát", "ầm ĩ", "yên tĩnh", "vọng", "tiếng kéo ghế"]
    },
    "AMBIENCE_COMFORT": {
        "main": "AMBIENCE",
        "keywords": ["thoải mái", "ấm cúng", "điều hòa", "quạt", "nóng", "bí", "mát", "nắng nóng"]
    },
    "AMBIENCE_DECOR": {
        "main": "AMBIENCE",
        "keywords": ["trang trí", "decor", "đẹp", "xinh", "dễ thương", "cổ", "view", "thiết kế", "không gian đẹp"]
    },
    "AMBIENCE_SEATING": {
        "main": "AMBIENCE",
        "keywords": ["bàn ghế", "chỗ ngồi", "không gian", "chật", "rộng", "bệt", "chật chội"]
    },
    "PRICE_VALUE_FOR_MONEY": {
        "main": "PRICE",
        "keywords": ["giá", "tiền", "đắt", "rẻ", "phù hợp", "đáng đồng tiền", "chặt chém", "mắc", "hợp lý", "30k", "40k", "50k", "20k", "25k"]
    },
    "PRICE_PORTION_FAIRNESS": {
        "main": "PRICE",
        "keywords": ["giá so với", "khẩu phần", "đĩa nhỏ giá cao", "đắt so với"]
    },
    "PRICE_PROMOTION": {
        "main": "PRICE",
        "keywords": ["voucher", "khuyến mãi", "giảm giá", "mã", "tặng", "free", "miễn phí", "combo"]
    },
    "PRICE_HIDDEN_COST": {
        "main": "PRICE",
        "keywords": ["phụ thu", "gửi xe", "phí", "tiền gửi xe"]
    }
}

def split_sentences(text):
    """Splits a paragraph into a list of sentences."""
    return re.split(r'[.!?;]|\n', text)

def extract_evidence(sentences, keyword):
    """Finds the first sentence containing the keyword to act as evidence."""
    keyword_clean = keyword.lower()
    for s in sentences:
        if keyword_clean in s.lower():
            # Clean spaces and return
            return s.strip()
    return ""

def rule_based_analysis(review):
    """Runs keyword matching on the review and returns multiple aspect records if matched."""
    content = review["content"]
    rating = review["rating"]  # 0 or 1
    sentences = split_sentences(content)
    
    aspects_found = []
    content_lower = content.lower()
    
    # Check each subcategory in our taxonomy
    for sub, info in KEYWORD_TAXONOMY.items():
        matched_keywords = [kw for kw in info["keywords"] if kw in content_lower]
        
        if matched_keywords:
            # We matched this subcategory!
            # Pick the first matched keyword to find evidence
            evidence = extract_evidence(sentences, matched_keywords[0])
            if not evidence:
                evidence = matched_keywords[0]
            
            # Determine sentiment score (-1.0 to 1.0)
            # If CSV Rating is 1 (Positive), sentiment is 0.5 or 1.0
            # If CSV Rating is 0 (Negative), sentiment is -0.5 or -1.0
            if rating == 1:
                sentiment = 0.5
                # Boost to 1.0 if strong words are matched
                if any(w in content_lower for w in ["ngon nhất", "cực ngon", "tuyệt vời", "xuất sắc", "yêu thích", "quá ngon", "ghiền", "max ngon", "chắc chắn quay lại", "max nhiệt tình"]):
                    sentiment = 1.0
                severity = 1
            else:
                sentiment = -0.5
                # Boost to -1.0 if extremely negative words are matched
                if any(w in content_lower for w in ["cực tệ", "quá tệ", "tệ hại", "kinh khủng", "eo ôi", "thảm họa", "ngộ độc", "nhiễm khuẩn", "không bao giờ quay lại", "kbh quay lại"]):
                    sentiment = -1.0
                
                # Determine Severity Score (1 to 5)
                severity = 3  # Default negative severity
                if any(w in content_lower for w in ["ngộ độc", "nhiễm khuẩn", "dị vật", "urgo", "nằm viện", "smecta", "cấp cứu", "đau bụng đi ngoài"]):
                    severity = 5  # Critical
                elif any(w in content_lower for w in ["đợi hơn", "chờ hơn", "1 tiếng", "40 phút", "chặt chém", "bố láo", "tệ hại"]):
                    severity = 4  # High
                elif any(w in content_lower for w in ["phục vụ hơi", "hơi chậm", "món hơi", "hơi nguội", "lèo tèo"]):
                    severity = 2  # Low

            # Set confidence high since this is rule-based keyword match
            confidence = round(0.85 + 0.1 * len(matched_keywords) / 10, 2)
            if confidence > 0.95:
                confidence = 0.95
                
            aspects_found.append({
                "review_id": review["review_id"],
                "branch_id": review["branch_id"],
                "branch_name": review.get("branch_name", "Unknown"),
                "source": review["source"],
                "sentiment": sentiment,
                "main_category": info["main"],
                "subcategory": sub,
                "severity": severity,
                "confidence": confidence,
                "evidence": evidence,
                "content": content,
                "created_at": review["created_at"]
            })
            
    # If no aspects were matched, assign OTHER
    if not aspects_found:
        if rating == 1:
            sentiment = 0.5
            severity = 1
        else:
            sentiment = -0.5
            severity = 2
            
        aspects_found.append({
            "review_id": review["review_id"],
            "branch_id": review["branch_id"],
            "branch_name": review.get("branch_name", "Unknown"),
            "source": review["source"],
            "sentiment": sentiment,
            "main_category": "OTHER",
            "subcategory": "OTHER",
            "severity": severity,
            "confidence": 0.8,
            "evidence": content[:50].strip() + ("..." if len(content) > 50 else ""),
            "content": content,
            "created_at": review["created_at"]
        })
        
    return aspects_found

def main():
    print(f"Loading cleaned reviews from {INPUT_PATH}...")
    if not os.path.exists(INPUT_PATH):
        print(f"Error: {INPUT_PATH} not found. Please run preprocess.py first.")
        return
        
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        reviews = json.load(f)
        
    total_reviews = len(reviews)
    print(f"Loaded {total_reviews} reviews. Running rule-based aspect analysis...")
    
    analyzed_records = []
    for r in tqdm(reviews):
        records = rule_based_analysis(r)
        analyzed_records.extend(records)
        
    print(f"Generated {len(analyzed_records)} analyzed aspect records (from {total_reviews} reviews).")
    
    # Save to JSON
    print(f"Saving to {OUTPUT_JSON_PATH}...")
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(analyzed_records, f, ensure_ascii=False, indent=2)
        
    # Save to CSV
    print(f"Saving to {OUTPUT_CSV_PATH}...")
    df = pd.DataFrame(analyzed_records)
    # Sort by created_at ascending
    df = df.sort_values(by="created_at").reset_index(drop=True)
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
    
    print("\n--- Rule-based Analysis Complete ---")
    print(f"Final output records count: {len(df)}")
    print("\nSample Output:")
    print(df.head(3).to_string())
    
    # Show main category distribution
    print("\nMain Category Distribution:")
    print(df['main_category'].value_counts())

if __name__ == "__main__":
    main()
