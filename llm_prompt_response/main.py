import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def load_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def process_contract(raw_text_path, output_path):
    # 1. 프롬프트 및 원본 데이터 로드
    system_prompt = load_file('prompts/cleaning_prompt.txt')
    raw_contract_data = load_file(raw_text_path)

    # 2. OpenAI API 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini", # 비용 효율적인 모델 추천
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"정제할 데이터는 다음과 같아:\n\n{raw_contract_data}"}
        ],
        response_format={ "type": "json_object" } # JSON 출력 강제
    )

    # 3. 결과 저장
    result = response.choices[0].message.content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"정제 완료: {output_path}")

# 실행 예시
raw_dir = Path('data/raw')
processed_dir = Path('data/processed')

for raw_file in raw_dir.glob('*.txt'):
    processed_file = processed_dir / f"{raw_file.stem}.json"
    process_contract(raw_file, processed_file)

# process_contract('data/raw/page_3400499247_body_text.txt', 'data/processed/result_3400499247.json')