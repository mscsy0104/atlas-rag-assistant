# coding=utf-8
"""
HTML 파일에서 모든 태그를 제거하고 텍스트만 추출하는 스크립트
"""
from bs4 import BeautifulSoup
from pathlib import Path
import sys


def extract_text_from_html(html_path: Path, separator: str = ' ', strip: bool = True) -> str:
    """
    HTML 파일에서 모든 태그를 제거하고 텍스트만 추출
    
    Args:
        html_path: HTML 파일 경로
        separator: 텍스트 요소 사이의 구분자 (기본값: 공백)
        strip: 각 텍스트 요소의 앞뒤 공백 제거 여부 (기본값: True)
        
    Returns:
        추출된 텍스트 문자열
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 모든 태그 제거하고 텍스트만 추출
    text = soup.get_text(separator=separator, strip=strip)
    
    return text


def extract_text_from_html_string(html_string: str, separator: str = ' ', strip: bool = True) -> str:
    """
    HTML 문자열에서 모든 태그를 제거하고 텍스트만 추출
    
    Args:
        html_string: HTML 문자열
        separator: 텍스트 요소 사이의 구분자 (기본값: 공백)
        strip: 각 텍스트 요소의 앞뒤 공백 제거 여부 (기본값: True)
        
    Returns:
        추출된 텍스트 문자열
    """
    soup = BeautifulSoup(html_string, 'html.parser')
    text = soup.get_text(separator=separator, strip=strip)
    return text


def save_text_to_file(text: str, output_path: Path):
    """
    추출된 텍스트를 파일로 저장
    
    Args:
        text: 저장할 텍스트
        output_path: 출력 파일 경로
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Text saved to {output_path}")


def process_all_body_html_files(data_path: Path):
    """
    data 폴더에서 모든 _body.html 파일을 찾아 텍스트를 추출하고 저장
    
    Args:
        data_path: data 폴더 경로
    """
    # 모든 _body.html 파일 찾기
    html_files = list(data_path.rglob('*_body.html'))
    
    if not html_files:
        print(f"No *_body.html files found in {data_path}")
        return
    
    print(f"Found {len(html_files)} HTML files to process\n")
    
    success_count = 0
    error_count = 0
    
    for html_file in html_files:
        try:
            # 텍스트 추출
            text = extract_text_from_html(html_file)
            
            # 같은 폴더에 _text.txt 파일로 저장
            output_file = html_file.parent / f"{html_file.stem}_text.txt"
            
            # 파일로 저장
            save_text_to_file(text, output_file)
            
            print(f"  ✓ {html_file.name}")
            print(f"    → {output_file.name} ({len(text)} characters)\n")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error processing {html_file.name}: {e}\n")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Processing complete:")
    print(f"  - Success: {success_count}")
    print(f"  - Errors: {error_count}")
    print(f"{'='*60}")


def main():
    """
    명령줄 인자로 HTML 파일 경로를 받아 텍스트만 추출하여 저장
    또는 data 폴더의 모든 _body.html 파일을 일괄 처리
    """
    # 인자가 없거나 '--all' 옵션이 있으면 data 폴더의 모든 _body.html 파일 처리
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == '--all'):
        data_path = Path('/Users/sychoi/ProjectInsightHub/fetch/data')
        if not data_path.exists():
            print(f"Error: Data path not found: {data_path}")
            sys.exit(1)
        process_all_body_html_files(data_path)
        return
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python parse_text_only_from_html.py --all")
        print("    Process all *_body.html files in data folder")
        print("  python parse_text_only_from_html.py <html_file_path> [output_file_path]")
        print("\nExample:")
        print("  python parse_text_only_from_html.py --all")
        print("  python parse_text_only_from_html.py page_3400499247_body.html page_3400499247_body.txt")
        print("  python parse_text_only_from_html.py page_3400499247_body.html")
        sys.exit(1)
    
    html_file = Path(sys.argv[1])
    
    if not html_file.exists():
        print(f"Error: File not found: {html_file}")
        sys.exit(1)
    
    # 텍스트 추출
    try:
        text = extract_text_from_html(html_file)
        
        # 출력 파일 경로 지정
        if len(sys.argv) > 2:
            output_file = Path(sys.argv[2])
        else:
            # 입력 파일과 같은 디렉토리에 .txt 확장자로 저장
            output_file = html_file.parent / f"{html_file.stem}_text.txt"
        
        # 파일로 저장
        save_text_to_file(text, output_file)
        
        print(f"\n✓ Successfully extracted text from {html_file}")
        print(f"  - Output: {output_file}")
        print(f"  - Text length: {len(text)} characters")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()