# coding=utf-8
"""
HTML 파일에서 모든 태그를 제거하고 텍스트만 추출하는 스크립트
"""
from bs4 import BeautifulSoup
from pathlib import Path
import traceback


def extract_text_from_html(html_path: Path, separator: str = ' ', strip: bool = True) -> str:
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=separator, strip=strip)
    
    return text


def extract_text_from_html_string(html_string: str, separator: str = ' ', strip: bool = True) -> str:
    soup = BeautifulSoup(html_string, 'html.parser')
    text = soup.get_text(separator=separator, strip=strip)
    return text


def save_text_to_file(text: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"{len(text)} characters Text saved to {output_path}")


def main():
    html_body_dir = Path('/Users/sychoi/ProjectInsightHub/data/fetched/html_body')
    processed_dir = Path('/Users/sychoi/ProjectInsightHub/data/processed')
    
    try:
        for html_path in html_body_dir.glob('*.html'):
            if not html_path.exists():
                continue
                
            text = extract_text_from_html(html_path)
            output_path = processed_dir / html_path.stem / f"{html_path.stem}_text.txt"
            save_text_to_file(text, output_path)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()