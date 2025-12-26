import csv
import json
import re
from pathlib import Path
from typing import List


def extract_table_number(filename: str) -> int:
    """CSV 파일명에서 테이블 번호를 추출합니다."""
    match = re.search(r'table_(\d+)\.csv$', filename)
    if match:
        return int(match.group(1))
    return 0


def read_csv_file(filepath: str) -> List[List[str]]:
    """CSV 파일을 읽어서 리스트로 반환합니다."""
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows


def format_table_csv(rows: List[List[str]], table_num: int) -> str:
    """CSV 데이터를 규칙에 맞게 포맷팅합니다."""
    if not rows:
        return ""
    
    # 첫 줄이 설명인지 확인
    first_row = rows[0]
    has_description = False
    
    # 첫 줄이 "이 표는"으로 시작하는지 확인 (따옴표 제거 후 확인)
    if first_row and len(first_row) > 0 and isinstance(first_row[0], str):
        first_cell = first_row[0].strip()
        # 따옴표로 감싸져 있는 경우 제거
        if first_cell.startswith('"') and first_cell.endswith('"'):
            first_cell = first_cell[1:-1]
        if first_cell.startswith("이 표는"):
            has_description = True
    
    result_lines = []
    
    # 헤더 추가
    result_lines.append(f"### [Table {table_num}] ###")
    result_lines.append("")
    
    # 설명이 없으면 기본 설명 추가
    if not has_description:
        description_row = ['"이 표는 상세내역임."']
        # 나머지 컬럼은 빈 값으로 채움
        if len(rows) > 0:
            num_cols = len(rows[0])
            description_row = ['"이 표는 상세내역임."'] + [''] * (num_cols - 1)
        result_lines.append(','.join(description_row))
    
    # CSV 데이터 추가
    for row in rows:
        # 각 셀을 적절히 처리 (따옴표 처리 확인)
        formatted_row = []
        for cell in row:
            cell_str = str(cell) if cell is not None else ''
            # 이미 따옴표로 감싸져 있지 않고, 콤마나 따옴표가 포함된 경우 따옴표로 감싸기
            if cell_str and not (cell_str.startswith('"') and cell_str.endswith('"')):
                if ',' in cell_str or '"' in cell_str or '\n' in cell_str:
                    # 따옴표를 이스케이프하고 전체를 따옴표로 감싸기
                    cell_str = '"' + cell_str.replace('"', '""') + '"'
            formatted_row.append(cell_str)
        result_lines.append(','.join(formatted_row))
    
    return '\n'.join(result_lines)


def process_page_tables(page_dir: Path) -> str:
    """한 페이지의 모든 테이블을 처리하여 하나의 문자열로 반환합니다."""
    table_dir = page_dir / "table"
    
    if not table_dir.exists():
        return ""
    
    # CSV 파일 목록 가져오기
    csv_files = list(table_dir.glob("*.csv"))
    
    if not csv_files:
        return ""
    
    # 파일명에서 테이블 번호 추출하여 정렬
    csv_files.sort(key=lambda x: extract_table_number(x.name))
    
    # 각 테이블 처리
    table_strings = []
    for csv_file in csv_files:
        table_num = extract_table_number(csv_file.name)
        rows = read_csv_file(str(csv_file))
        formatted_table = format_table_csv(rows, table_num)
        if formatted_table:
            table_strings.append(formatted_table)
            # 구분선 추가 (마지막 테이블이 아닌 경우)
            if csv_file != csv_files[-1]:
                table_strings.append("---")
    
    # 체크박스 처리 가이드 추가
    guide_text = "\n**표 안의 'complete/incomplete'는 해당 항목의 선택 여부를   **"
    
    # 모든 테이블을 합치기
    result = '\n\n'.join(table_strings)
    result = result + guide_text
    
    return result


def main():
    """메인 함수: 모든 페이지의 테이블을 처리하여 JSONL 파일로 저장합니다."""
    processed_dir = Path("/Users/sychoi/ProjectInsightHub/data/processed")

    if not processed_dir.exists():
        print(f"Error: {processed_dir} 디렉토리가 존재하지 않습니다.")
        return
    
    # 모든 page_xxx_body 디렉토리 찾기
    page_dirs = [d for d in processed_dir.iterdir() if d.is_dir() and d.name.startswith("page_") and d.name.endswith("_body")]
    
    if not page_dirs:
        print("처리할 페이지 디렉토리를 찾을 수 없습니다.")
        return
    
    # 결과를 저장할 리스트
    results = []

    for page_dir in page_dirs:
        # page_id 추출 (예: page_3400499247_body -> 3400499247)
        page_id_match = re.search(r'page_(\d+)_body', page_dir.name)
        if not page_id_match:
            print(f"Warning: {page_dir.name}에서 page_id를 추출할 수 없습니다.")
            continue
        
        page_id = page_id_match.group(1)
        output_file = processed_dir / "merged_tables.jsonl"
        existing_ids = []

        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = json.loads(line)
                    existing_ids.append(line['page_id'])

            if page_id in existing_ids:
                print(f"Page {page_id} already exists in {output_file}")
                continue

        print(f"Processing page_id: {page_id}")
        
        # 테이블 처리
        table_string = process_page_tables(page_dir)
        
        if table_string:
            results.append({
                "page_id": page_id,
                "value": table_string
            })
        else:
            print(f"Warning: {page_id}에 대한 테이블 데이터가 없습니다.")
    
    # JSONL 파일로 저장
    with open(output_file, 'a', encoding='utf-8') as f:
        for result in results:
            json_line = json.dumps(result, ensure_ascii=False)
            f.write(json_line + '\n')
    
    print(f"\n완료: {len(results)}개의 페이지가 처리되어 {output_file}에 저장되었습니다.")


if __name__ == "__main__":
    main()

