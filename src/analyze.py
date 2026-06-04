import os
import sys
import json
import time
import random
import argparse
from datetime import datetime
import pandas as pd
from tqdm import tqdm
import google.generativeai as genai
import google.api_core.exceptions

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    os.makedirs("logs", exist_ok=True)
    with open("logs/analysis.log", "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

# Config paths
INPUT_PATH = "data/processed/cleaned_reviews.json"
OUTPUT_JSON_PATH = "data/processed/analyzed_reviews.json"
OUTPUT_CSV_PATH = "data/processed/analyzed_reviews.csv"
CHECKPOINT_PATH = "data/processed/analyzed_reviews_checkpoint.json"

# Taxonomy list for prompt instructions
TAXONOMY_DESC = """
1. FOOD:
   - FOOD_TASTE: Món ngon, dở, nhạt, đậm vị, vừa miệng...
   - FOOD_FRESHNESS: Độ tươi ngon, mùi lạ, thực phẩm cũ, ôi thiu...
   - FOOD_TEMPERATURE: Món nóng, nguội, lạnh, không đúng nhiệt độ...
   - FOOD_PORTION: Khẩu phần nhiều, ít, không đều, đầy đặn...
   - FOOD_PRESENTATION: Cách trình bày, bắt mắt, đĩa to/nhỏ...
2. SERVICE:
   - SERVICE_WAIT_TIME: Đợi lâu, lên món chậm, làm món nhanh...
   - SERVICE_STAFF_ATTITUDE: Thái độ nhân viên (nhiệt tình, niềm nở, khó chịu, gắt gỏng)...
   - SERVICE_ACCURACY: Mang nhầm món, thiếu món, làm sai order...
   - SERVICE_RESPONSIVENESS: Phản hồi chậm, không hỗ trợ, lờ đi yêu cầu...
   - SERVICE_PROFESSIONALISM: Tác phong, quy trình, tính tiền chuyên nghiệp/chậm, xử lý tình huống...
3. AMBIENCE:
   - AMBIENCE_CLEANLINESS: Vệ sinh bàn, sàn, toilet, dụng cụ ăn uống có tóc/bẩn...
   - AMBIENCE_NOISE: Ồn ào, âm thanh khó chịu, nhạc hay/dở...
   - AMBIENCE_COMFORT: Sự thoải mái, nhiệt độ phòng (điều hòa mát/nóng), ánh sáng...
   - AMBIENCE_DECOR: Trang trí, không gian đẹp, ấm cúng, view đẹp, sạch sẽ sáng sủa...
   - AMBIENCE_SEATING: Chỗ ngồi, bàn ghế, sắp xếp bàn, chật chội/rộng rãi...
4. PRICE:
   - PRICE_VALUE_FOR_MONEY: Đáng tiền hay không, đắt, rẻ, đáng đồng tiền bát gạo...
   - PRICE_PORTION_FAIRNESS: Giá so với khẩu phần (đĩa nhỏ giá cao)...
   - PRICE_PROMOTION: Voucher, khuyến mãi, mã giảm giá, airpay...
   - PRICE_HIDDEN_COST: Phụ thu, phí không rõ, phí gửi xe...
5. OTHER:
   - OTHER: Không xác định hoặc nằm ngoài các khía cạnh trên.
"""

PROMPT_TEMPLATE = """
Bạn là một trợ lý AI chuyên phân tích phản hồi của khách hàng cho chuỗi nhà hàng ăn uống.
Nhiệm vụ của bạn là phân tích danh sách {batch_size} reviews dưới đây và phân loại chúng theo đúng mô hình dữ liệu (Taxonomy) và thang điểm quy định.

### TAXONOMY (Main Category & Subcategory)
{taxonomy_desc}

### SCORING FRAMEWORK
1. Sentiment Score (float):
   - `-1.0`: Rất tiêu cực (chửi bới, ngộ độc, cực kỳ tệ, tẩy chay)
   - `-0.5`: Tiêu cực (chê bai, không hài lòng)
   - `0.0`: Trung lập (không khen không chê, chỉ mô tả sự việc)
   - `0.5`: Tích cực (khen ngợi, hài lòng, ổn)
   - `1.0`: Rất tích cực (rất ngon, cực kỳ thích, 10/10, xuất sắc, chắc chắn quay lại)

2. Severity Score (int - Mức độ nghiêm trọng của vấn đề, từ 1 đến 5):
   - `1`: Minor (Vấn đề nhỏ, ví dụ: "Món hơi nguội", hoặc các phản hồi tích cực/khen ngợi)
   - `2`: Low (Ví dụ: "Phục vụ hơi chậm")
   - `3`: Medium (Ví dụ: "Đợi 30 phút mới có món")
   - `4`: High (Ví dụ: "Đợi hơn 1 giờ", hoặc thái độ cực kỳ thiếu tôn trọng)
   - `5`: Critical (Ví dụ: "Ngộ độc thực phẩm", có dị vật bẩn như miếng dán thương tích, nhiễm trùng nhập viện)
   *Lưu ý:* Mặc định gán `1` cho các phản hồi Tích cực hoặc Rất tích cực (Sentiment >= 0).

3. Confidence (float):
   - Độ tự tin của bạn khi phân loại (từ `0.0` đến `1.0`).

4. Evidence (string):
   - Trích dẫn ngắn, chính xác các từ/cụm từ gốc trong review làm bằng chứng cho phân loại trên. Không tự bịa ra từ ngữ.

### NGUYÊN TẮC QUAN TRỌNG: MULTI-ASPECT
Nếu một review nhắc đến NHIỀU khía cạnh khác nhau (ví dụ: đồ ăn ngon nhưng phục vụ chậm, hoặc vừa khen đồ ăn vừa khen không gian "ngon, sạch"), bạn phải tạo NHIỀU analyzed records cho review_id đó, mỗi record tương ứng với một subcategory khác nhau.

### OUTPUT FORMAT
Yêu cầu trả về duy nhất một mảng JSON (JSON array of objects) theo cấu trúc dưới đây. Không thêm bất kỳ văn bản giải thích nào ngoài JSON.
Schema:
[
  {{
    "review_id": "string",
    "sentiment": float,
    "main_category": "FOOD" | "SERVICE" | "AMBIENCE" | "PRICE" | "OTHER",
    "subcategory": "string",
    "severity": int,
    "confidence": float,
    "evidence": "string"
  }}
]

### DANH SÁCH REVIEWS CẦN PHÂN TÍCH:
{reviews_text}
"""

class GeminiClientManager:
    """Manages rotation of Gemini API keys from a file to avoid rate limits."""
    def __init__(self, key_file="apikey.txt"):
        self.keys = []
        try:
            with open(key_file, "r") as f:
                self.keys = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        except FileNotFoundError:
            pass
            
        # Fallback to env var if file not found or empty
        if not self.keys:
            env_key = os.environ.get("GEMINI_API_KEY")
            if env_key:
                self.keys = [env_key]
                
        if not self.keys:
            raise ValueError(f"No Gemini API keys found in {key_file} or GEMINI_API_KEY environment variable.")
            
        self.current_idx = 0
        print(f"Loaded {len(self.keys)} API keys for rotation.")
        
    def get_next_client(self):
        idx = self.current_idx
        key = self.keys[idx]
        # Rotate index for next call
        self.current_idx = (self.current_idx + 1) % len(self.keys)
        # Force REST transport to bypass gRPC handshake hangs on certain networks
        genai.configure(api_key=key, transport="rest")
        # Use gemini-3.5-flash as requested by user
        model = genai.GenerativeModel('gemini-3.5-flash')
        key_repr = f"Key_{idx+1} ({key[:6]}...{key[-4:]})"
        return model, key_repr

def call_gemini_with_retry(manager, prompt, max_retries=6):
    """Calls Gemini API with client rotation and exponential backoff on HTTP 429."""
    # Ensure max_retries covers all available keys at least once
    actual_retries = max(max_retries, len(manager.keys) * 2)
    
    for attempt in range(actual_retries):
        model, key_repr = manager.get_next_client()
        try:
            log_message(f"Sending batch request to Gemini API using {key_repr}...")
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1,  # Low temperature for deterministic classification
                },
                request_options={"timeout": 90.0}  # Increased timeout to 90s for gemini-3.5-flash batch classification
            )
            # Try parsing to make sure it's valid JSON before returning
            json_text = response.text.strip()
            # Clean possible markdown wrapping if returned
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            parsed = json.loads(json_text)
            log_message(f"Success! Received {len(parsed)} aspect records.")
            return parsed
            
        except google.api_core.exceptions.ResourceExhausted as e:
            # If we still have untried keys in the pool, switch immediately with a tiny delay
            if attempt < len(manager.keys):
                log_message(f"[Warning] Rate limit hit on {key_repr}. Switching API key immediately...")
                time.sleep(0.15)
            else:
                # If we have cycled through all keys, apply exponential backoff
                wait_time = (2 ** (attempt - len(manager.keys))) + random.uniform(0.5, 1.5)
                log_message(f"[Warning] All API keys have hit limits. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
        except google.api_core.exceptions.GoogleAPICallError as e:
            log_message(f"[Warning] Google API error on {key_repr}: {e}. Retrying with next key...")
            time.sleep(1)
        except json.JSONDecodeError:
            log_message(f"[Warning] Invalid JSON returned from model. Retrying request...")
            time.sleep(1)
        except Exception as e:
            log_message(f"[Warning] Unexpected error on {key_repr}: {e}. Retrying...")
            time.sleep(2)
            
    raise RuntimeError("Failed to process batch with Gemini API after max retries.")

def load_checkpoint():
    """Loads analyzed results and processed IDs from checkpoint or main JSON file."""
    # 1. Try loading from checkpoint first
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)
                if checkpoint_data:
                    print(f"Resuming from checkpoint. Loaded {len(checkpoint_data)} analyzed records.")
                    processed_ids = {r["review_id"] for r in checkpoint_data if "review_id" in r}
                    return checkpoint_data, processed_ids
        except Exception as e:
            print(f"Error reading checkpoint file: {e}. Trying main output file...")

    # 2. Fall back to the main output JSON file (in case checkpoint was cleaned up on completion)
    if os.path.exists(OUTPUT_JSON_PATH):
        try:
            with open(OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
                main_data = json.load(f)
                if main_data:
                    print(f"Resuming from main output file. Loaded {len(main_data)} analyzed records.")
                    processed_ids = {r["review_id"] for r in main_data if "review_id" in r}
                    return main_data, processed_ids
        except Exception as e:
            print(f"Error reading main output file: {e}. Starting fresh.")

    return [], set()

def save_checkpoint(data):
    """Saves analyzed results progress to checkpoint and main CSV/JSON files."""
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    # Save checkpoint JSON
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    # Also save progress to the main output CSV and JSON files immediately
    if data:
        # Sort using Python built-in key to avoid introducing float 'nan' from pandas
        sorted_records = sorted(data, key=lambda x: x.get("created_at", ""))
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted_records, f, ensure_ascii=False, indent=2)
        # Save sorted CSV
        df = pd.DataFrame(sorted_records)
        df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")

def main():
    parser = argparse.ArgumentParser(description="Batch analyze cleaned reviews using Gemini API and key rotation.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of reviews to process (for testing).")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of reviews to process per API request.")
    parser.add_argument("--checkpoint-interval", type=int, default=1, help="Save checkpoint every N batches.")
    args = parser.parse_args()

    # Load cleaned reviews
    if not os.path.exists(INPUT_PATH):
        print(f"Error: {INPUT_PATH} not found. Run preprocess.py first.")
        sys.exit(1)
        
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        reviews = json.load(f)
    print(f"Loaded {len(reviews)} cleaned reviews.")

    # Apply limit if specified
    if args.limit:
        reviews = reviews[:args.limit]
        print(f"Limiting execution to the first {len(reviews)} reviews.")

    # Initialize client manager (loads apikey.txt)
    try:
        manager = GeminiClientManager("apikey.txt")
    except Exception as e:
        print(f"Initialization Error: {e}")
        sys.exit(1)

    # Load progress from checkpoint
    analyzed_records, processed_ids = load_checkpoint()

    # Create mapping of review_id -> review metadata for merging later
    # This allows us to re-inject branch_id and created_at fields into the output records
    review_metadata = {r["review_id"]: {
        "branch_id": r["branch_id"],
        "branch_name": r.get("branch_name", "Unknown"),
        "source": r.get("source", "unknown"),
        "rating": r.get("rating", 1),
        "content": r["content"],
        "created_at": r["created_at"]
    } for r in reviews}

    # Filter out reviews that are already processed in checkpoint
    reviews_to_process = [r for r in reviews if r["review_id"] not in processed_ids]
    total_to_process = len(reviews_to_process)
    
    if total_to_process == 0:
        print("All reviews are already analyzed. No work to do.")
    else:
        print(f"Remaining reviews to process: {total_to_process}")
        
        # Process in batches
        batch_size = args.batch_size
        batches = [reviews_to_process[i:i + batch_size] for i in range(0, total_to_process, batch_size)]
        
        batches_completed = 0
        
        for batch_idx, batch in enumerate(tqdm(batches, desc="Analyzing reviews")):
            batch_ids = [r['review_id'] for r in batch]
            log_message(f"Processing Batch {batch_idx + 1}/{len(batches)} (Size: {len(batch)}): {batch_ids[0]} to {batch_ids[-1]}")
            
            # Format reviews text block for the prompt
            reviews_text_list = []
            for r in batch:
                reviews_text_list.append(f"ID: {r['review_id']}\nContent: \"{r['content']}\"")
            reviews_text = "\n\n".join(reviews_text_list)
            
            prompt = PROMPT_TEMPLATE.format(
                batch_size=len(batch),
                taxonomy_desc=TAXONOMY_DESC,
                reviews_text=reviews_text
            )
            
            try:
                # Call API (will rotate keys and retry on 429 rate limit)
                batch_results = call_gemini_with_retry(manager, prompt)
                
                # Verify and merge metadata (branch_id, created_at)
                for record in batch_results:
                    rev_id = record.get("review_id")
                    if rev_id in review_metadata:
                        # Inject original metadata fields
                        record["branch_id"] = review_metadata[rev_id]["branch_id"]
                        record["branch_name"] = review_metadata[rev_id]["branch_name"]
                        record["source"] = review_metadata[rev_id]["source"]
                        record["rating"] = review_metadata[rev_id]["rating"]
                        record["content"] = review_metadata[rev_id]["content"]
                        record["created_at"] = review_metadata[rev_id]["created_at"]
                        analyzed_records.append(record)
                    else:
                        log_message(f"[Warning] Unknown review_id returned by model: {rev_id}")
                        
                batches_completed += 1
                
                # Checkpoint save
                if batches_completed % args.checkpoint_interval == 0:
                    save_checkpoint(analyzed_records)
                    log_message(f"Backup progress auto-saved (Checkpoint size: {len(analyzed_records)} records).")
                    
            except Exception as e:
                print(f"\n[Error] Terminated batch due to persistent errors: {e}")
                print("Saving progress to checkpoint before exiting...")
                save_checkpoint(analyzed_records)
                sys.exit(1)

    # Save final results
    if analyzed_records:
        # Sort using Python built-in key to avoid introducing float 'nan' from pandas
        sorted_records = sorted(analyzed_records, key=lambda x: x.get("created_at", ""))
        
        # Save to JSON
        print(f"Saving final results to JSON: {OUTPUT_JSON_PATH}...")
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted_records, f, ensure_ascii=False, indent=2)
            
        # Convert to DataFrame and save to CSV
        print(f"Saving final results to CSV: {OUTPUT_CSV_PATH}...")
        df = pd.DataFrame(sorted_records)
        df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")
        
        # Clean up checkpoint on full completion
        if total_to_process > 0 and os.path.exists(CHECKPOINT_PATH):
            os.remove(CHECKPOINT_PATH)
            print("Checkpoint cleaned up.")
            
        print(f"\n--- Analysis Complete ---")
        print(f"Total analyzed records generated: {len(analyzed_records)}")
        print(f"Result files:")
        print(f"  - CSV: {OUTPUT_CSV_PATH}")
        print(f"  - JSON: {OUTPUT_JSON_PATH}")
    else:
        print("No analyzed records generated.")

if __name__ == "__main__":
    main()
