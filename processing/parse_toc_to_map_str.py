from bs4 import BeautifulSoup as bs
from pathlib import Path
import re
import json


def parse_html(html_path: Path) -> bs:
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = bs(html, 'html.parser')
    return soup


def extract_top_level_toc(soup, page_id: str, processed_dir: Path):
    """제일 상단 목차만 추출하여 '1. 프로젝트 개요 > 2. 작업 내용 > ...' 형식으로 JSON에 저장"""
    toc_filename = "html_body_toc.jsonl"
    toc_path = processed_dir / toc_filename
    
    existing_ids = []
    if toc_path.exists():
        with open(toc_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = json.loads(line)
                existing_ids.append(line['page_id'])

    if page_id in existing_ids:
        print(f"Page {page_id} already exists in {toc_path.relative_to(processed_dir.parent)}")
        return

    # 모든 h2 태그를 순서대로 찾기
    headings = []
    for h2 in soup.find_all('h2'):
        # 테이블, 리스트 내부가 아닌 최상위 요소만 추출
        if h2.find_parent(['table', 'ul', 'ol']):
            continue
        
        # 텍스트 추출
        text = h2.get_text(separator=' ', strip=True)
        
        if not text:
            continue
        
        # 숫자로 시작하는 헤딩만 추출 (예: "1. 프로젝트 개요", "2. 작업 내용")
        # 패턴: 숫자 + 점 + 공백으로 시작하는 경우
        if re.match(r'^\d+\.\s+', text):
            headings.append(text)
    
    if not headings:
        print(f"No top-level TOC found for page {page_id}")
        return
    
    # "1. 프로젝트 개요 > 2. 작업 내용 > ..." 형식으로 변환
    toc_string = ' > '.join(headings)
    
    # JSON 파일로 저장 (키: 문서 페이지, 값: toc)
    toc_data = {
        'page_id': page_id,
        'toc': toc_string
    }

    with open(toc_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(toc_data, ensure_ascii=False))
        f.write('\n')
    
    print(f"Saved TOC to {toc_path.relative_to(processed_dir.parent)}")


def main():
    data_path = Path('/Users/sychoi/ProjectInsightHub/data')
    html_body_dir = data_path / 'fetched' / 'html_body'
    html_body_dir.mkdir(parents=True, exist_ok=True)
    
    processed_dir = data_path / 'processed'

    for html_path in html_body_dir.glob('*.html'):
        if not html_path.exists():
            continue
            
        soup = parse_html(html_path)
        
        # page_id 추출 (예: page_3126853834_body -> 3126853834)
        
        page_id = html_path.stem.replace('page_', '').replace('_body', '')

        # 제일 상단 목차 추출 (JSON)
        extract_top_level_toc(soup, page_id, processed_dir)


if __name__ == '__main__':
    main()

