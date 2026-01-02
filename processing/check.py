import json
from pathlib import Path

def extract_keys_from_jsonl(file_path):
    all_keys = set()
    
    with open(toc_path,'r', encoding='utf-8') as f:
        for line in f:
            try:
                line = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line.strip()}")

            if isinstance(line, dict):
                page_id = line.get('page_id')
                if page_id and isinstance(page_id, str):
                    page_id = int(line.get('page_id'))
                    print(page_id)
                    all_keys.add(page_id)

    return all_keys

toc_path = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/html_body_toc.jsonl')
keys = extract_keys_from_jsonl(toc_path)
print(f"Extracted keys: {keys}")