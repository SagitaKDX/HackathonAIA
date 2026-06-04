import pandas as pd
import numpy as np
import re
import json
import random
import unicodedata
from datetime import datetime, timedelta
import emoji

# Config
INPUT_PATH = "data/raw/data_spa.csv"
OUTPUT_CSV_PATH = "data/processed/cleaned_reviews.csv"
OUTPUT_JSON_PATH = "data/processed/cleaned_reviews.json"

# List of branches from spec/spec.md and their match keywords
BRANCHES = [
    {"branch_id": "branch_nguyen_hue", "branch_name": "Nguyễn Huệ", "keywords": ["nguyễn huệ", "nguyen hue"]},
    {"branch_id": "branch_times_city", "branch_name": "Times City", "keywords": ["times city", "time city"]},
    {"branch_id": "branch_aeon_mall_ha_dong", "branch_name": "Aeon Mall Hà Đông", "keywords": ["aeon mall", "aeon", "hà đông"]},
    {"branch_id": "branch_ly_quoc_su", "branch_name": "Lý Quốc Sư", "keywords": ["lý quốc sư", "ly quoc su"]},
    {"branch_id": "branch_hang_bo", "branch_name": "Hàng Bồ", "keywords": ["hàng bồ", "hang bo"]},
    {"branch_id": "branch_vo_chi_cong", "branch_name": "Võ Chí Công", "keywords": ["võ chí công", "vo chi cong"]},
    {"branch_id": "branch_cau_giay", "branch_name": "Cầu Giấy", "keywords": ["cầu giấy", "cau giay"]},
    {"branch_id": "branch_vincom", "branch_name": "Vincom", "keywords": ["vincom"]},
    {"branch_id": "branch_kim_nguu", "branch_name": "Kim Ngưu", "keywords": ["kim ngưu", "kim nguu"]},
    {"branch_id": "branch_truong_dinh", "branch_name": "Trương Định", "keywords": ["trương định", "truong dinh"]},
    {"branch_id": "branch_giai_phong", "branch_name": "Giải Phóng", "keywords": ["giải phóng", "giai phong"]},
    {"branch_id": "branch_nguyen_chi_thanh", "branch_name": "Nguyễn Chí Thanh", "keywords": ["nguyễn chí thanh", "nguyen chi thanh"]},
]

# Mapping of Vietnamese slang, abbreviations, and common typos
SLANG_MAP = {
    "ko": "không",
    "k": "không",
    "kh": "không",
    "khg": "không",
    "khôngg": "không",
    "ngonnn": "ngon",
    "ngonnnn": "ngon",
    "chánnn": "chán",
    "tệee": "tệ",
    "đc": "được",
    "dc": "được",
    "dược": "được",
    "nv": "nhân viên",
    "pv": "phục vụ",
    "mn": "mọi người",
    "mng": "mọi người",
    "chg": "cửa hàng",
    "gđ": "gia định",  # gia đình
    "vc": "vợ chồng",
    "vs": "với",
    "kbbf": "King BBQ",
    "ts": "trà sữa",
    "bf": "buffet",
    "hn": "Hà Nội",
    "sg": "Sài Gòn",
    "qc": "quảng cáo",
    "review": "đánh giá",
    "cực": "rất",
    "chán": "tệ",
    "chả": "không",
    "ncl": "nói chung là",
    "nhứt": "nhất",
    "chổ": "chỗ",
    "đông đông": "đông",
    "đới": "đó",
    "rùi": "rồi",
    "oke": "ổn",
    "ok": "ổn",
    "oks": "ổn",
    "thui": "thôi",
    "hic": "tiếc",
    "hix": "tiếc",
    "hoá ra": "hóa ra",
    "hoá": "hóa",
    "hùi": "hồi",
    "trc": "trước",
    "mìnhh": "mình",
    "mún": "muốn",
    "iu": "yêu",
    "đag": "đang",
    "ib": "nhắn tin",
    "fb": "Facebook",
    "sdt": "số điện thoại",
    "p/s": "tái bút",
    "ps": "tái bút",
    "khs": "không hiểu sao",
    "od": "order",
    "order": "đặt món",
    "oder": "đặt món",
    "ship": "giao hàng",
    "shipper": "người giao hàng",
    "buffee": "buffet",
    "cream": "kem",
    "cheese": "phô mai",
    "dessert": "tráng miệng",
    "decor": "trang trí",
    "view": "tầm nhìn",
    "wifi": "mạng wifi",
}

# Emoji normalization mapping to descriptive tags
EMOJI_MAP = {
    "😊": " [hài lòng] ",
    "🙂": " [tạm ổn] ",
    "😀": " [vui vẻ] ",
    "😁": " [vui vẻ] ",
    "😂": " [cười] ",
    "🤣": " [cười] ",
    "😍": " [rất thích] ",
    "🥰": " [yêu thích] ",
    "😘": " [yêu thích] ",
    "😋": " [ngon miệng] ",
    "👍": " [tốt/khuyên dùng] ",
    "❤️": " [yêu thích] ",
    "💖": " [yêu thích] ",
    "💕": " [yêu thích] ",
    "👏": " [khen ngợi] ",
    "🎉": " [chúc mừng] ",
    "😭": " [rất tệ/thất vọng] ",
    "😢": " [thất vọng] ",
    "😞": " [thất vọng] ",
    "😡": " [tức giận] ",
    "😠": " [tức giận] ",
    "🤮": " [ngộ độc/kinh tởm] ",
    "🤢": " [ngộ độc/kinh tởm] ",
    "👎": " [tệ/không khuyên dùng] ",
    "⭐": " [sao] ",
    "✨": " [tuyệt vời] ",
    "🔥": " [nổi bật] ",
}

def remove_repeated_chars(text):
    """Reduces characters repeated 3 or more times (e.g., ngonnn -> ngon, quáaaa -> quá)."""
    return re.sub(r'(\w)\1{2,}', r'\1', text)

def normalize_text(text):
    """Cleans slang, typos, abbreviations, unicode, and double spaces."""
    if not isinstance(text, str):
        return ""
    
    # Normalize unicode to NFC (standard Vietnamese representation)
    text = unicodedata.normalize('NFC', text)
    
    # Remove excessive repeated chars (e.g. ngonnn -> ngon)
    text = remove_repeated_chars(text)
    
    # Simple word tokenization and slang replacement
    words = text.split()
    normalized_words = []
    for word in words:
        # Strip common punctuation to check against slang dictionary
        clean_word = word.strip(".,!?;:()\"'[]{}*~-_@#$%^&+=<>/")
        clean_word_lower = clean_word.lower()
        
        if clean_word_lower in SLANG_MAP:
            mapped = SLANG_MAP[clean_word_lower]
            # Reattach the original prefix and suffix punctuation
            prefix = word[:word.find(clean_word)]
            suffix = word[word.find(clean_word) + len(clean_word):]
            word = prefix + mapped + suffix
            
        normalized_words.append(word)
        
    cleaned_text = " ".join(normalized_words)
    return re.sub(r'\s+', ' ', cleaned_text).strip()

def normalize_emojis(text):
    """Replaces emojis with textual descriptions or standard formats."""
    if not isinstance(text, str):
        return ""
    
    cleaned_chars = []
    for char in text:
        if char in EMOJI_MAP:
            cleaned_chars.append(EMOJI_MAP[char])
        elif emoji.is_emoji(char):
            # Demojize other emojis and format them as [tag]
            tag_name = emoji.demojize(char).replace(':', '').replace('_', ' ')
            cleaned_chars.append(f" [{tag_name}] ")
        else:
            cleaned_chars.append(char)
            
    res = "".join(cleaned_chars)
    return re.sub(r'\s+', ' ', res).strip()

def extract_branch(text, index):
    """Matches text to a branch based on keywords. If none match, assigns cyclically."""
    text_lower = text.lower()
    for branch in BRANCHES:
        for keyword in branch["keywords"]:
            if keyword in text_lower:
                return branch["branch_id"], branch["branch_name"]
    # Fallback to cyclic assignment to ensure equal distribution of missing labels
    fallback_branch = BRANCHES[index % len(BRANCHES)]
    return fallback_branch["branch_id"], fallback_branch["branch_name"]

def determine_source(text):
    """Assigns source based on text content (e.g. mentions of delivery apps, maps, etc.)."""
    text_lower = text.lower()
    
    # Food delivery keywords
    if any(k in text_lower for k in ["ship", "giao", "shopeefood", "grabfood", "grab", "now", "app", "đặt về", "delivery"]):
        return random.choice(["shopeefood", "grabfood"])
    
    # Maps and local keywords
    if any(k in text_lower for k in ["google", "maps", "bản đồ", "địa chỉ", "đường", "vị trí", "tìm thấy"]):
        return "google_maps"
        
    # Social media keywords
    if any(k in text_lower for k in ["facebook", "fb", "page", "group", "bài viết", "post"]):
        return "facebook"
        
    # Fallback with realistic weights
    sources = ["google_maps", "facebook", "shopeefood", "grabfood", "internal_feedback"]
    weights = [0.4, 0.2, 0.2, 0.15, 0.05]
    return random.choices(sources, weights=weights)[0]

def generate_timestamp(index, total_rows):
    """Generates realistic timestamps distributed over the last 30 days."""
    # Today's date from system is 2026-06-04
    base_date = datetime(2026, 6, 4, 12, 0, 0)
    # Distribute times over the last 30 days
    days_offset = 30.0 * (index / max(total_rows - 1, 1))
    # Add a tiny random jitter (up to 2 hours) to avoid perfectly spaced dates
    jitter_seconds = random.randint(-7200, 7200)
    
    timestamp = base_date - timedelta(days=days_offset) + timedelta(seconds=jitter_seconds)
    # Format with standard timezone offset (+07:00 as in plan)
    return timestamp.strftime("%Y-%m-%dT%H:%M:%S+07:00")

def main():
    print(f"Loading raw reviews from {INPUT_PATH}...")
    try:
        df = pd.read_csv(INPUT_PATH)
    except FileNotFoundError:
        print(f"Error: {INPUT_PATH} not found. Please place it in data/raw/")
        return
        
    initial_count = len(df)
    print(f"Loaded {initial_count} records.")

    # Drop null rows in comments or ratings
    df = df.dropna(subset=['Comment', 'Rating'])
    print(f"Filtered out empty values. Count: {len(df)}")
    
    # Remove duplicate reviews
    df = df.drop_duplicates(subset=['Comment'])
    print(f"Filtered out duplicates. Count: {len(df)}")
    
    # Keep the content original as requested
    df['content'] = df['Comment']
    
    # Remove rows where comment is empty or too short (e.g. < 4 chars)
    df = df[df['content'].str.len() >= 4]
    print(f"Filtered out very short/empty reviews. Count: {len(df)}")
    
    # Reset index to allow correct calculations for timestamps/branches
    df = df.reset_index(drop=True)
    total_rows = len(df)
    
    # Generate schema fields
    print("Generating schema metadata...")
    
    # 1. Review ID: rev_XXXXX
    df['review_id'] = [f"rev_{i+1:05d}" for i in range(total_rows)]
    
    # 2. Rating mapping:
    # Keep the original binary rating (0 or 1) from the dataset as requested
    df['rating'] = df['Rating']
    
    # 3. Branch extraction & mapping
    branches_extracted = [extract_branch(comment, idx) for idx, comment in enumerate(df['content'])]
    df['branch_id'] = [b[0] for b in branches_extracted]
    df['branch_name'] = [b[1] for b in branches_extracted]
    
    # 4. Source mapping
    df['source'] = df['content'].apply(determine_source)
    
    # 5. Timestamp generation
    df['created_at'] = [generate_timestamp(idx, total_rows) for idx in range(total_rows)]
    
    # Select columns matching Raw Review schema
    schema_cols = ['review_id', 'branch_id', 'branch_name', 'source', 'rating', 'content', 'created_at']
    cleaned_df = df[schema_cols]
    
    # Sort by created_at ascending (oldest first)
    cleaned_df = cleaned_df.sort_values(by='created_at').reset_index(drop=True)
    
    # Save to CSV
    print(f"Saving cleaned reviews to CSV: {OUTPUT_CSV_PATH}...")
    cleaned_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
    
    # Save to JSON
    print(f"Saving cleaned reviews to JSON: {OUTPUT_JSON_PATH}...")
    json_records = cleaned_df.to_dict(orient='records')
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(json_records, f, ensure_ascii=False, indent=2)
        
    print("\n--- Preprocessing Complete ---")
    print(f"Initial raw rows: {initial_count}")
    print(f"Final cleaned rows: {total_rows}")
    print(f"Removed {(initial_count - total_rows)} rows of duplicates/empty/short/spam.")
    print("\nSample records:")
    print(cleaned_df.head(2).to_string())
    
    # Show branch distribution
    print("\nBranch Distribution:")
    print(cleaned_df['branch_name'].value_counts())
    
    # Show rating distribution
    print("\nRating Distribution:")
    print(cleaned_df['rating'].value_counts())
    
    # Show source distribution
    print("\nSource Distribution:")
    print(cleaned_df['source'].value_counts())

if __name__ == "__main__":
    main()
