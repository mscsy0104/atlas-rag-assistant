import json
from pathlib import Path

metadata_dir = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/metadata')
processed_dir = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed')
output_file = processed_dir / 'merged_metadata.jsonl'
for file in metadata_dir.iterdir():
    print(file)

    with open(file, 'r', encoding='utf-8') as f:
        obj = json.load(f)
        print(obj)
    # obj['page_id'] = obj.pop('id')

    # print(obj)

    with open(output_file, 'a', encoding='utf-8') as of:
        json.dump(obj, of, ensure_ascii=False)
        of.write('\n')
