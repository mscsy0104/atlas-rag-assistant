from dotenv import load_dotenv
from pathlib import Path
import re
import json

load_dotenv()


def load_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def extract_page_id_from_filename(filename):
    match = re.search(r'page_(\d+)_body_text', filename)
    if match:
        return int(match.group(1))
    else:
        raise ValueError(f"Invalid filename: {filename}")

def process_contract(raw_text_path, output_path):
    # 1. OpenAI 답변 불러오기
    print(output_path)
    response = None
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            response = json.load(f)
            print(response)

    if response is None:
        print("Error: No response data available")
        return

    page_id = extract_page_id_from_filename(raw_text_path.stem)
    print(f"Page ID: {page_id}")
    result = {
        "page_id": page_id,
        "content": response
    }

    # 2. 결과 저장
    try:
        result = json.dumps(result, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error: {e}")
        return

    print(result)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"정제 완료: {output_path}")

# 실행 예시
raw_dir = Path('data/raw')
processed_dir = Path('data/processed')

for raw_file in raw_dir.glob('*.txt'):
    processed_file = processed_dir / f"{raw_file.stem}.json"
    process_contract(raw_file, processed_file)