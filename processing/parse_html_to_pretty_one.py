from bs4 import BeautifulSoup as bs
from pathlib import Path

data_path = Path('/Users/sychoi/ProjectInsightHub/data')
fetched_dir = data_path / 'fetched'
processed_dir = data_path / 'processed'
html_body_dir = fetched_dir / 'html_body'


def parse_html(html_path: Path) -> bs:
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = bs(html, 'html.parser')
    return soup


def main():
    # data/processed 아래의 모든 page_*_body 폴더에서 _body.html 파일 찾기
    for html_path in html_body_dir.glob('*.html'):
        html_path = Path(html_path)
        
        if not html_path.exists():
            continue
        
        # _pretty.html 파일은 건너뛰기
        if '_pretty' in html_path.stem:
            continue
            
        soup = parse_html(html_path)
        pretty_html = soup.prettify()
        
        # 같은 폴더에 _pretty.html 저장
        page_dir = processed_dir / html_path.stem
        page_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = page_dir / f"{page_dir.stem}_pretty.html"
    
        # 예쁜 HTML 저장
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(pretty_html)
            print(f"Saved pretty HTML to {output_path}")
            print()

if __name__ == '__main__':
    main()