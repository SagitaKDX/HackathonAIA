import os
import json
import pandas as pd

CLEANED_PATH = "data/processed/cleaned_reviews.json"

# 1. Load cleaned reviews mapping (review_id -> content)
if not os.path.exists(CLEANED_PATH):
    print("Error: cleaned_reviews.json not found!")
    exit(1)

with open(CLEANED_PATH, "r", encoding="utf-8") as f:
    cleaned = json.load(f)

content_map = {r["review_id"]: r["content"] for r in cleaned if "review_id" in r and "content" in r}
print(f"Loaded {len(content_map)} content mappings.")

files_to_fix_json = [
    "data/processed/analyzed_reviews_checkpoint.json",
    "data/processed/analyzed_reviews.json"
]

for file_path in files_to_fix_json:
    if os.path.exists(file_path):
        try:
            print(f"Fixing JSON file: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            modified = False
            for r in data:
                rev_id = r.get("review_id")
                if "content" not in r or not r["content"]:
                    r["content"] = content_map.get(rev_id, r.get("evidence", ""))
                    modified = True
            
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"Successfully updated {file_path}")
            else:
                print(f"No changes needed for {file_path}")
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")

csv_path = "data/processed/analyzed_reviews.csv"
if os.path.exists(csv_path):
    try:
        print(f"Fixing CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        
        modified = False
        if "content" not in df.columns:
            df["content"] = df["review_id"].map(content_map).fillna(df["evidence"])
            modified = True
        else:
            mask = df["content"].isna() | (df["content"] == "")
            if mask.any():
                df.loc[mask, "content"] = df.loc[mask, "review_id"].map(content_map).fillna(df.loc[mask, "evidence"])
                modified = True
                
        if modified:
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"Successfully updated {csv_path}")
        else:
            print(f"No changes needed for {csv_path}")
    except Exception as e:
        print(f"Error fixing {csv_path}: {e}")
