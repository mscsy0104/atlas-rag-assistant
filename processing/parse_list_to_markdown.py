# coding=utf-8
"""
HTML 리스트를 Markdown 파일로 변환하는 모듈
"""
from bs4 import BeautifulSoup
from pathlib import Path

data_path = Path('/Users/sychoi/ProjectInsightHub/data')
fetched_dir = data_path / 'fetched'
processed_dir = data_path / 'processed'
html_body_dir = fetched_dir / 'html_body'


def find_list_context(list, soup) -> str:
    """
    리스트 앞의 컨텍스트(헤딩, 제목 등)를 찾아 반환
    
    Args:
        list: BeautifulSoup 리스트 요소 (ul 또는 ol)
        soup: BeautifulSoup 전체 문서 객체
        
    Returns:
        컨텍스트 텍스트 (없으면 빈 문자열)
    """
    context = ""

    # 1. expand 매크로의 title 찾기 (리스트가 expand 안에 있는 경우)
    expand_macro = list.find_parent('ac:structured-macro', {'ac:name': 'expand'})
    if expand_macro:
        title_param = expand_macro.find('ac:parameter', {'ac:name': 'title'})
        if title_param and title_param.string:
            context = title_param.string.strip()
            if context:
                return context
    
    # 2. 리스트 이전의 가장 가까운 헤딩 찾기
    all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol'])
    for i, elem in enumerate(all_elements):
        if elem == list:
            # 현재 리스트의 위치를 찾았으므로, 이전 요소들을 역순으로 확인
            for j in range(i - 1, -1, -1):
                prev_elem = all_elements[j]
                if prev_elem.name and prev_elem.name.startswith('h'):
                    # 헤딩을 찾았으면 텍스트 추출
                    heading_text = prev_elem.get_text(separator=' ', strip=True)
                    if heading_text:
                        # strong 태그 제거하고 텍스트만 추출
                        heading_text = ' '.join(heading_text.split())
                        return heading_text
                elif prev_elem.name == 'ul' or prev_elem.name == 'ol':
                    # 다른 리스트를 만나면 중단
                    break
            break
    
    # 3. 리스트의 부모 요소에서 제목 찾기
    parent = list.parent
    if parent:
        prev_sibling = parent.previous_sibling
        while prev_sibling:
            if hasattr(prev_sibling, 'name'):
                if prev_sibling.name and prev_sibling.name.startswith('h'):
                    heading_text = prev_sibling.get_text(separator=' ', strip=True)
                    if heading_text:
                        return ' '.join(heading_text.split())
            prev_sibling = prev_sibling.previous_sibling if hasattr(prev_sibling, 'previous_sibling') else None
    
    return context


def list_to_markdown(list_elem, level: int = 0, context: str = "") -> str:
    """
    HTML 리스트를 Markdown 형식의 문자열로 변환 (중첩 리스트 포함)
    
    Args:
        list_elem: BeautifulSoup 리스트 요소 (ul 또는 ol)
        level: 현재 리스트 레벨 (들여쓰기용)
        context: 리스트의 컨텍스트 텍스트 (선택사항)
        
    Returns:
        Markdown 형식의 문자열
    """
    markdown_lines = []
    indent = "  " * level  # 레벨당 2칸 들여쓰기

    # 컨텍스트가 있으면 맨 위에 추가
    if context:
        markdown_lines.append(f"이 리스트는 {context} 조항에 대한 상세내역임.")
        markdown_lines.append("")  # 빈 줄 추가
    
    # 리스트 타입 확인 (ordered 또는 unordered)
    is_ordered = list_elem.name == 'ol'
    
    # 리스트의 직접 자식 li만 찾기 (중첩된 리스트는 재귀적으로 처리)
    li_items = list_elem.find_all('li', recursive=False)
    
    for idx, li in enumerate(li_items, 1):
        # 현재 항목의 텍스트 추출 (직접 자식 텍스트만)
        item_text = ''
        for content in li.contents:
            if isinstance(content, str):
                item_text += content.strip() + ' '
            elif content.name not in ['ul', 'ol']:
                text = content.get_text(separator=' ', strip=True)
                if text:
                    item_text += text + ' '
        
        item_text = item_text.strip()
        
        if not item_text:
            continue
        
        # Markdown 리스트 항목 생성
        if is_ordered:
            markdown_item = f"{indent}{idx}. {item_text}"
        else:
            markdown_item = f"{indent}- {item_text}"
        
        markdown_lines.append(markdown_item)
        
        # 중첩된 리스트가 있는지 확인
        nested_lists = li.find_all(['ul', 'ol'], recursive=False)
        if nested_lists:
            # 중첩된 리스트를 재귀적으로 처리
            for nested_list in nested_lists:
                nested_markdown = list_to_markdown(nested_list, level + 1)
                if nested_markdown:
                    markdown_lines.append(nested_markdown)
    
    return '\n'.join(markdown_lines)


def extract_lists_to_markdown(soup, output_prefix: str, page_dir: Path):
    """
    HTML의 모든 리스트를 Markdown 파일로 저장
    
    Args:
        soup: BeautifulSoup 객체
        output_prefix: 출력 파일명 접두사 (예: page_3126853834_body)
        page_dir: 페이지 디렉토리 경로 (예: data/processed/page_3126853834_body)
    """
    # 테이블 내부가 아닌 최상위 리스트만 찾기
    lists = []
    for list_elem in soup.find_all(['ul', 'ol']):
        # 테이블 내부에 있는 리스트는 제외 (테이블에서 이미 처리됨)
        if not list_elem.find_parent('table'):
            lists.append(list_elem)
    
    if not lists:
        print(f"No lists found in {output_prefix}")
        return
    
    # list 하위 폴더 생성
    list_dir = page_dir / "list"
    list_dir.mkdir(parents=True, exist_ok=True)
    
    for idx, list_elem in enumerate(lists, 1):
        # 리스트의 컨텍스트 찾기
        context = find_list_context(list_elem, soup)
        
        markdown_content = list_to_markdown(list_elem, context=context)
        
        if not markdown_content.strip():
            continue
        
        # Markdown 파일명 생성: page_<page_id>_body_list_<순서번호>.md
        md_filename = f"{output_prefix}_list_{idx}.md"
        
        md_path = list_dir / md_filename
        
        # Markdown 파일로 저장
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Saved list {idx} to {md_path.relative_to(page_dir.parent)}")
        print(f"  Content length: {len(markdown_content)} characters")


def parse_list_to_markdown(html_path: Path, output_dir: Path = None):
    """
    HTML 파일에서 리스트를 추출하여 Markdown 파일로 저장
    
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
    extract_lists_to_markdown(soup, output_prefix, output_dir)


def main():
    """data/processed 아래의 모든 page_*_body 폴더에서 HTML 파일을 찾아 리스트 추출"""
    for html_path in html_body_dir.glob('*.html'):
        html_path = Path(html_path)
        
        if not html_path.exists():
            continue
        
        page_dir = processed_dir / html_path.stem
        page_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {html_path.name}...")
        parse_list_to_markdown(html_path, page_dir)


if __name__ == '__main__':
    main()
