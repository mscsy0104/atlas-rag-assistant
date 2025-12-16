# coding=utf-8
"""
Confluence page JSON 파일의 storage 내용을 파싱하여 구조화된 데이터로 변환하는 스크립트
"""
import json
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Any


def parse_storage_content(storage_html: str) -> Dict[str, Any]:
    """
    Confluence storage 형식의 HTML/XML을 파싱하여 구조화된 데이터로 변환
    
    Args:
        storage_html: Confluence storage 형식의 HTML/XML 문자열
        
    Returns:
        구조화된 데이터 딕셔너리
    """
    soup = BeautifulSoup(storage_html, 'html.parser')
    
    parsed_data = {
        'sections': [],
        'tables': [],
        'lists': [],
        'macros': [],
        'links': [],
        'images': [],
        'plain_text': []
    }
    
    # 섹션(헤딩) 추출
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        section = {
            'level': int(heading.name[1]),
            'text': heading.get_text(strip=True),
            'content': []
        }
        
        # 헤딩 다음 요소들 수집
        next_elements = []
        current = heading.next_sibling
        while current:
            # if current.name and current.name.startswith('h') and int(current.name[1]) <= section['level']:
            if current.name and current.name.startswith('h') and current.name[1].isdigit():
                if int(current.name[1]) <= section['level']:
                    break
            if current.name:
                next_elements.append(current)
            current = current.next_sibling
        
        # 다음 요소들의 텍스트 추출
        for elem in next_elements:
            if elem.name == 'p':
                section['content'].append({
                    'type': 'paragraph',
                    'text': elem.get_text(strip=True)
                })
            elif elem.name in ['ul', 'ol']:
                section['content'].append({
                    'type': 'list',
                    'items': [li.get_text(strip=True) for li in elem.find_all('li', recursive=False)]
                })
            elif elem.name == 'table':
                section['content'].append(parse_table(elem))
        
        parsed_data['sections'].append(section)
    
    # 테이블 추출
    for table in soup.find_all('table'):
        parsed_data['tables'].append(parse_table(table))
    
    # 리스트 추출
    for ul in soup.find_all(['ul', 'ol']):
        items = []
        for li in ul.find_all('li', recursive=False):
            items.append({
                'text': li.get_text(strip=True),
                'sub_items': [sub_li.get_text(strip=True) for sub_li in li.find_all('li', recursive=False)]
            })
        parsed_data['lists'].append({
            'type': 'ordered' if ul.name == 'ol' else 'unordered',
            'items': items
        })
    
    # 매크로 추출
    for macro in soup.find_all('ac:structured-macro'):
        macro_data = {
            'name': macro.get('ac:name', ''),
            'parameters': {}
        }
        for param in macro.find_all('ac:parameter'):
            param_name = param.get('ac:name', '')
            param_value = param.get_text(strip=True)
            macro_data['parameters'][param_name] = param_value
        parsed_data['macros'].append(macro_data)
    
    # 링크 추출
    for link in soup.find_all('a'):
        parsed_data['links'].append({
            'text': link.get_text(strip=True),
            'href': link.get('href', '')
        })
    
    # 이미지 추출
    for img in soup.find_all('ac:image'):
        attachment = img.find('ri:attachment')
        if attachment:
            parsed_data['images'].append({
                'filename': attachment.get('ri:filename', ''),
                'alt': img.get('ac:alt', '')
            })
    
    # 일반 텍스트 추출 (헤딩, 테이블, 리스트 제외)
    for p in soup.find_all('p'):
        if not any(p.find_parent(tag) for tag in ['table', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = p.get_text(strip=True)
            if text:
                parsed_data['plain_text'].append(text)
    
    return parsed_data


def parse_table(table) -> Dict[str, Any]:
    """테이블을 파싱하여 구조화된 데이터로 변환"""
    rows = []
    headers = []
    
    # 헤더 추출
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    
    # 본문 행 추출
    tbody = table.find('tbody') or table
    for tr in tbody.find_all('tr'):
        cells = []
        for td in tr.find_all(['td', 'th']):
            cell_text = td.get_text(strip=True)
            # 셀 내부에 리스트가 있는 경우
            cell_lists = td.find_all(['ul', 'ol'])
            if cell_lists:
                cell_data = {
                    'text': cell_text,
                    'lists': []
                }
                for ul in cell_lists:
                    cell_data['lists'].append([li.get_text(strip=True) for li in ul.find_all('li')])
                cells.append(cell_data)
            else:
                cells.append(cell_text)
        rows.append(cells)
    
    return {
        'headers': headers,
        'rows': rows
    }


def parse_json_file(json_file_path: str, output_file: str = None) -> Dict[str, Any]:
    """
    JSON 파일을 읽어서 storage 내용을 파싱
    
    Args:
        json_file_path: Confluence page JSON 파일 경로
        output_file: 파싱 결과를 저장할 파일 경로 (선택사항)
        
    Returns:
        파싱된 데이터
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        page_data = json.load(f)
    
    # Storage 내용 추출
    storage_value = page_data.get('body', {}).get('storage', {}).get('value', '')
    
    if not storage_value:
        print("Storage content not found in JSON file")
        return {}
    
    # 파싱
    parsed_data = parse_storage_content(storage_value)
    
    # 페이지 메타데이터 추가
    result = {
        'page_id': page_data.get('id'),
        'page_title': page_data.get('title'),
        'parsed_content': parsed_data
    }
    
    # 결과 저장
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        print(f"Parsed data saved to {output_file}")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_confluence_storage.py <json_file_path> [output_file_path]")
        print("\nExample:")
        print("  python parse_confluence_storage.py page_3341123699.json page_3341123699_parsed.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not output_file:
        output_file = json_file.replace('.json', '_parsed.json')
    
    try:
        result = parse_json_file(json_file, output_file)
        print(f"\n✓ Successfully parsed {json_file}")
        print(f"  - Sections: {len(result.get('parsed_content', {}).get('sections', []))}")
        print(f"  - Tables: {len(result.get('parsed_content', {}).get('tables', []))}")
        print(f"  - Lists: {len(result.get('parsed_content', {}).get('lists', []))}")
        print(f"  - Macros: {len(result.get('parsed_content', {}).get('macros', []))}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

