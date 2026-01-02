import json
from pathlib import Path

processed_llm_resps_dir = Path('/Users/sychoi/projects/ProjectInsightHub/llm_prompt_response/data/processed')
processed_dir = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed')
output_file = processed_dir / 'merged_llm_resps.jsonl'
for file in processed_llm_resps_dir.iterdir():
    print(file)

    with open(file, 'r', encoding='utf-8') as f:
        obj = json.load(f)
        print(obj)
    # obj['page_id'] = obj.pop('id')

    # print(obj)

    with open(output_file, 'a', encoding='utf-8') as of:
        json.dump(obj, of, ensure_ascii=False)
        of.write('\n')
