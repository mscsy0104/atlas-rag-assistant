import json
from pathlib import Path
from collections import defaultdict
import re


def extract_table_captions(table_data):
    """
    table_data에서 테이블 캡션/설명을 추출합니다.
    table_data는 다음 중 하나일 수 있습니다:
    - dict: {'page_id': str, 'value': str} 형태
    - list: dict들의 리스트
    - str: 이미 파싱된 JSON 문자열
    """
    if not table_data:
        return ""
    
    captions = []
    
    # table_data가 리스트인 경우
    if isinstance(table_data, list):
        for item in table_data:
            if isinstance(item, dict):
                # 'value' 필드에서 테이블 설명 추출
                value = item.get('value', '')
                if value:
                    captions.extend(_extract_descriptions_from_table_value(value))
            elif isinstance(item, str):
                # JSON 문자열인 경우 파싱 시도
                try:
                    obj = json.loads(item)
                    if isinstance(obj, dict) and 'value' in obj:
                        captions.extend(_extract_descriptions_from_table_value(obj['value']))
                except Exception:
                    continue
    
    # table_data가 dict인 경우
    elif isinstance(table_data, dict):
        value = table_data.get('value', '')
        if value:
            captions.extend(_extract_descriptions_from_table_value(value))
    
    # table_data가 문자열인 경우 (JSON 문자열 또는 직접 테이블 데이터)
    elif isinstance(table_data, str):
        try:
            obj = json.loads(table_data)
            if isinstance(obj, dict) and 'value' in obj:
                captions.extend(_extract_descriptions_from_table_value(obj['value']))
        except Exception:
            # JSON이 아닌 경우 직접 처리 (테이블 데이터 문자열)
            captions.extend(_extract_descriptions_from_table_value(table_data))
    
    # 중복 제거하고 반환
    unique_captions = []
    seen = set()
    for caption in captions:
        if caption and caption not in seen:
            unique_captions.append(caption)
            seen.add(caption)
    
    return "; ".join(unique_captions)


def _extract_descriptions_from_table_value(value: str) -> list:
    """
    테이블 value 문자열에서 설명 부분을 추출합니다.
    "이 표는 ... 조항에 대한 상세내역임." 형태의 설명을 찾습니다.
    """
    descriptions = []
    if not value:
        return descriptions
    
    lines = value.split('\n')
    for line in lines:
        line = line.strip()
        # "이 표는"으로 시작하는 설명 라인 찾기
        if line.startswith('이 표는') or (line.startswith('"이 표는') and '"이 표는' in line):
            # 따옴표 제거
            line = line.strip('"').strip("'")
            # "조항에 대한 상세내역" 또는 유사한 패턴으로 끝나는지 확인
            if '상세내역' in line or '조항' in line:
                # 불필요한 부분 제거 (CSV 형식의 나머지 컬럼 제거)
                description = line.split(',')[0].strip('"').strip()
                if description:
                    descriptions.append(description)
    
    return descriptions


def make_vector_content(merged_obj):
    """
    검색용 벡터 콘텐츠를 생성합니다.
    
    Args:
        merged_obj: 모든 데이터 소스가 병합된 dict 객체
            - 'title' 또는 'id': 제목
            - 'content': LLM 응답 dict (내부에 'summary' 포함)
            - 'toc': 문서 구조 문자열
            - 'value': 테이블 데이터 문자열
    """
    # 제목 추출
    title = merged_obj.get('title', '')
    
    # 문서 개요 추출 (LLM 응답의 content.summary)
    summary = ""
    content = merged_obj.get('content', {})
    if isinstance(content, dict):
        summary = content.get('summary', '')
    
    # 문서 구조(TOC) 추출
    toc_str = merged_obj.get('toc', '')
    
    # 테이블 캡션 추출
    table_data = merged_obj.get('value', '')
    table_captions = extract_table_captions(table_data)
    
    # 섹션 구성
    sections = [
        f"제목: {title}",
        f"문서 개요: {summary}",
        f"문서 구조: {toc_str}",
        f"포함된 표 내용: {table_captions}"
    ]
    
    # 빈 섹션 제거하고 조인
    non_empty_sections = [s for s in sections if s.split(':', 1)[-1].strip()]
    
    return "\n".join(non_empty_sections)

def get_obj_from_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = json.loads(line)

            data.append(line)
    return data

def get_obj_from_dir(dir_path):
    data = []
    for file in dir_path.iterdir():
        with open(file, 'r', encoding='utf-8') as f:
            data.append(json.load(f))
    return data

def extract_page_id_from_basename(basename):
    match = re.search(r'page_(\d+)_body_text', basename)
    if match:
        return int(match.group(1))
    else:
        raise ValueError(f"Invalid basename: {basename}")

def extract_page_ids_from_dir(dir_path):
    page_ids = []
    for file in dir_path.iterdir():
        page_id = extract_page_id_from_basename(file.stem)
        page_ids.append(page_id)
    
    return page_ids

def extract_page_ids_from_jsonl(file_path):
    page_ids = set()
    
    with open(file_path,'r', encoding='utf-8') as f:
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
                    page_ids.add(page_id)

    return page_ids

def main():
    # data sources
    merged_tables_path = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/merged_tables.jsonl')
    toc_path = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/html_body_toc.jsonl')
    merged_metadata_path = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/merged_metadata.jsonl')
    merged_llm_resps_path = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/merged_llm_resps.jsonl')

    table_data = get_obj_from_jsonl(merged_tables_path)
    toc = get_obj_from_jsonl(toc_path)
    metadata = get_obj_from_jsonl(merged_metadata_path)
    llm_responses = get_obj_from_jsonl(merged_llm_resps_path)

    data_sources = {
        "metadata": metadata,
        "toc": toc,
        "table_data": table_data,
        "llm_responses": llm_responses
    }

    main_map = defaultdict(dict)
    presence_check = defaultdict(set)

    for src_name, data in data_sources.items():
        for obj in data:
            pid = str(obj.get('page_id') or obj.get('id'))
            if not pid:
                continue

            main_map[pid].update(obj)
            # # 예시: defaultdict(<class 'dict'>, {'1111': {'summary': '본 계약서는 ...'}})
            presence_check[pid].add(src_name)
            # # 예시: defaultdict(<class 'set'>, {'1111': {'metadata', 'table_data', ...}})

    final_data_sources = []
    incomplete_objs = []
    src_names_set = set(data_sources.keys())
    print(f'src_names_set: {src_names_set}')

    for pid, found_sources in presence_check.items():
        missing = src_names_set - found_sources

        if not missing:
            final_data_sources.append(main_map[pid])
        else:
            incomplete_obj = main_map[pid]
            incomplete_obj['missing_sources'] = list(missing)
            incomplete_objs.append(incomplete_obj)

    # 결과 리포트
    print(f"✅ 완전한 객체 (RAG Ready): {len(final_data_sources)}개")
    print(f"⚠️ 누락 발생 객체: {len(incomplete_objs)}개")

    # 누락 상세 확인 (예시)
    if incomplete_objs:
        print(f"첫 번째 누락 예시 (ID: {incomplete_objs[0].get('page_id') or incomplete_objs[0].get('id')}): {incomplete_objs[0]['missing_sources']} 소스 없음")
    
    # RAG를 위한 vector content 생성
    output_path = Path('/Users/sychoi/projects/ProjectInsightHub/data/processed/vector_contents.jsonl')
    vector_contents = []
    
    print("\n📝 Vector content 생성 중...")
    for merged_obj in final_data_sources:
        page_id = str(merged_obj.get('page_id') or merged_obj.get('id', ''))
        vector_content = make_vector_content(merged_obj)
        
        vector_contents.append({
            'page_id': page_id,
            'vector_content': vector_content,
            'metadata': {
                'title': merged_obj.get('title', '')
            }
        })
    
    # JSONL 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in vector_contents:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"✅ Vector content 생성 완료: {len(vector_contents)}개")
    print(f"📁 저장 위치: {output_path}")
    
    # 첫 번째 예시 출력
    if vector_contents:
        print("\n📄 첫 번째 Vector Content 예시:")
        print(f"Page ID: {vector_contents[0]['page_id']}")
        print(f"Title: {vector_contents[0]['metadata']['title']}")
        print(f"\n{vector_contents[0]['vector_content']}")
        print("-" * 80)


if __name__ == '__main__':
    main()

    
