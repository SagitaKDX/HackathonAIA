import os
import re
import json

files_to_clean = [
    "data/processed/analyzed_reviews.json",
    "data/processed/analyzed_reviews_checkpoint.json"
]

for file_path in files_to_clean:
    if os.path.exists(file_path):
        print(f"Cleaning NaN values in: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace literal : NaN with : null (makes it valid JSON)
            cleaned_content = re.sub(r':\s*NaN\b', ': null', content)
            
            # Parse and clean up keys containing null values
            data = json.loads(cleaned_content)
            for r in data:
                null_keys = [k for k, v in r.items() if v is None]
                for k in null_keys:
                    del r[k]
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Successfully cleaned {file_path}")
        except Exception as e:
            print(f"Error cleaning {file_path}: {e}")
