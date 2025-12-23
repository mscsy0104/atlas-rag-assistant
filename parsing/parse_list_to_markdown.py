# coding=utf-8
"""
HTML 리스트를 Markdown 파일로 변환하는 모듈
"""
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List


def list_to_markdown(list_elem, level: int = 0) -> str:
    """
    HTML 리스트를 Markdown 형식의 문자열로 변환 (중첩 리스트 포함)
    
    Args:
        list_elem: BeautifulSoup 리스트 요소 (ul 또는 ol)
        level: 현재 리스트 레벨 (들여쓰기용)
        
    Returns:
        Markdown 형식의 문자열
    """
    markdown_lines = []
    indent = "  " * level  # 레벨당 2칸 들여쓰기
    
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
        output_prefix: 출력 파일명 접두사
        page_dir: 페이지 디렉토리 경로
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
        markdown_content = list_to_markdown(list_elem)
        
        if not markdown_content.strip():
            continue
        
        # Markdown 파일명 생성
        if len(lists) == 1:
            md_filename = f"{output_prefix}_list.md"
        else:
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


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_list_to_markdown.py <html_file_path> [output_dir]")
        sys.exit(1)
    
    html_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    parse_list_to_markdown(html_file, output_dir)

