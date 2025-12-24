# coding=utf-8
"""
HTML 테이블을 CSV 파일로 변환하는 모듈
"""
from bs4 import BeautifulSoup
from pathlib import Path
import csv
from typing import List

data_path = Path('/Users/sychoi/ProjectInsightHub/data')
fetched_dir = data_path / 'fetched'
processed_dir = data_path / 'processed'
html_body_dir = fetched_dir / 'html_body'


def find_table_context(table, soup) -> str:
    """
    테이블 앞의 컨텍스트(헤딩, 제목 등)를 찾아 반환
    
    Args:
        table: BeautifulSoup 테이블 요소
        soup: BeautifulSoup 전체 문서 객체
        
    Returns:
        컨텍스트 텍스트 (없으면 빈 문자열)
    """
    context = ""
    
    # 1. expand 매크로의 title 찾기 (테이블이 expand 안에 있는 경우)
    expand_macro = table.find_parent('ac:structured-macro', {'ac:name': 'expand'})
    if expand_macro:
        title_param = expand_macro.find('ac:parameter', {'ac:name': 'title'})
        if title_param and title_param.string:
            context = title_param.string.strip()
            if context:
                return context
    
    # 2. 테이블 이전의 가장 가까운 헤딩 찾기
    all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table'])
    
    for i, elem in enumerate(all_elements):
        if elem == table:
            # 현재 테이블의 위치를 찾았으므로, 이전 요소들을 역순으로 확인
            for j in range(i - 1, -1, -1):
                prev_elem = all_elements[j]
                if prev_elem.name and prev_elem.name.startswith('h'):
                    # 헤딩을 찾았으면 텍스트 추출
                    heading_text = prev_elem.get_text(separator=' ', strip=True)
                    if heading_text:
                        # strong 태그 제거하고 텍스트만 추출
                        heading_text = ' '.join(heading_text.split())
                        return heading_text
                elif prev_elem.name == 'table':
                    # 다른 테이블을 만나면 중단
                    break
            break
    
    # 3. 테이블의 부모 요소에서 제목 찾기
    parent = table.parent
    if parent:
        # 부모의 이전 형제에서 헤딩 찾기
        prev_sibling = parent.previous_sibling
        while prev_sibling:
            if hasattr(prev_sibling, 'name'):
                if prev_sibling.name and prev_sibling.name.startswith('h'):
                    heading_text = prev_sibling.get_text(separator=' ', strip=True)
                    if heading_text:
                        return ' '.join(heading_text.split())
            prev_sibling = prev_sibling.previous_sibling if hasattr(prev_sibling, 'previous_sibling') else None
    
    return context


def table_to_csv_rows(table, context: str = "") -> List[List[str]]:
    """
    HTML 테이블을 CSV 행 리스트로 변환
    
    Args:
        table: BeautifulSoup 테이블 요소
        context: 테이블의 컨텍스트 텍스트 (선택사항)
        
    Returns:
        CSV 행 리스트 (각 행은 셀 문자열 리스트)
    """
    rows = []
    
    # 컨텍스트가 있으면 첫 번째 행으로 추가
    if context:
        # CSV 형식에 맞게 컨텍스트를 첫 번째 행으로 추가
        # 모든 컬럼에 걸쳐 표시하기 위해 첫 번째 컬럼에만 넣고 나머지는 빈 문자열
        # 하지만 실제 컬럼 수를 알기 전이므로, 일단 빈 리스트로 추가하고 나중에 처리
        pass
    
    # tbody가 있으면 tbody에서, 없으면 table에서 직접 찾기
    tbody = table.find('tbody') or table
    
    for tr in tbody.find_all('tr'):
        row = []
        for cell in tr.find_all(['td', 'th']):
            # 셀의 텍스트 추출 (리스트, 링크 등 포함)
            cell_text = cell.get_text(separator=' | ', strip=True)
            # 줄바꿈을 공백으로, 여러 공백을 하나로
            cell_text = ' '.join(cell_text.split())
            row.append(cell_text)
        if row:  # 빈 행이 아닌 경우만 추가
            rows.append(row)
    
    # 컨텍스트가 있고 행이 있으면, 첫 번째 행의 컬럼 수에 맞춰 컨텍스트 추가
    if context and rows:
        num_columns = len(rows[0])
        context_row = [f"이 표는 {context} 조항에 대한 상세내역임."] + [''] * (num_columns - 1)
        rows.insert(0, context_row)
    
    return rows


def extract_tables_to_csv(soup, output_prefix: str, page_dir: Path):
    """
    HTML의 모든 테이블을 CSV 파일로 저장
    
    Args:
        soup: BeautifulSoup 객체
        output_prefix: 출력 파일명 접두사 (예: page_3126853834_body)
        page_dir: 페이지 디렉토리 경로 (예: data/processed/page_3126853834_body)
    """
    tables = soup.find_all('table')
    
    if not tables:
        print(f"No tables found in {output_prefix}")
        return
    
    # table 하위 폴더 생성
    table_dir = page_dir / "table"
    table_dir.mkdir(parents=True, exist_ok=True)
    
    for idx, table in enumerate(tables, 1):
        # 테이블의 컨텍스트 찾기
        context = find_table_context(table, soup)
        
        csv_rows = table_to_csv_rows(table, context)
        
        if not csv_rows:
            continue
        
        # CSV 파일명 생성: page_<page_id>_body_table_<순서번호>.csv
        csv_filename = f"{output_prefix}_table_{idx}.csv"
        
        csv_path = table_dir / csv_filename
        
        # CSV 파일로 저장
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
        
        print(f"Saved table {idx} to {csv_path.relative_to(page_dir.parent)} ({len(csv_rows)} rows)")


def parse_table_to_csv(html_path: Path, output_dir: Path = None):
    """
    HTML 파일에서 테이블을 추출하여 CSV 파일로 저장
    
    Args:
        html_path: HTML 파일 경로
        output_dir: 출력 디렉토리 (None이면 HTML 파일과 같은 디렉토리)
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    if output_dir is None:
        output_dir = html_path.parent
    
    output_prefix = html_path.stem
    extract_tables_to_csv(soup, output_prefix, output_dir)


def main():    
    for html_path in html_body_dir.glob('*.html'):
        html_path = Path(html_path)
        
        if not html_path.exists():
            continue

        page_dir = processed_dir / html_path.stem
        page_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {html_path.name}...")
        parse_table_to_csv(html_path, page_dir)


if __name__ == '__main__':
    main()