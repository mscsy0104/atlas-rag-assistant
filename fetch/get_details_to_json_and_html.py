# coding=utf-8
from atlassian import Confluence
import os
import re
from dotenv import load_dotenv
from pathlib import Path
import json

load_dotenv()

ATLASSIAN_API_KEY = os.getenv("ATLASSIAN_API_KEY")
USERNAME = os.getenv("ATLASSIAN_USERNAME")


test_url_samples = [
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3341123699/EV_+_25+Data+Labeling",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3400499247/EN_+_LLM+Evaluation+dataset+FT",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3126853834/EN_+SDS_KB+AI+Data+Readiness",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3285745686/GOV_+_2024+Vision+AI+Document+AI",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/2955280541/EV_+_2024+1"
]



confluence = Confluence(
    url="https://crowdworksinc.atlassian.net/wiki", 
    username=USERNAME, 
    password=ATLASSIAN_API_KEY
    )

# Extract page IDs from URLs and get page data
def extract_page_id_from_url(url):
    """Extract page ID from Confluence URL"""
    match = re.search(r'/pages/(\d+)/', url)
    if match:
        return int(match.group(1))
    return None

# Get page data for all URLs in test_url_samples
for url in test_url_samples:
# for url in test_url_samples[:1]:
# for url in test_url_samples:
    page_id = extract_page_id_from_url(url)
    if page_id:
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print(f"Page ID: {page_id}")
        print(f"{'='*60}")
        try:
            # Get page with full body content
            # expand parameter includes the body content (storage format contains the full HTML/XML)
            content = confluence.get_page_by_id(
                page_id=page_id,
                expand='body.storage,body.view,version'
            )
            print(type(content))

            with open(f"page_{page_id}.json", "w", encoding="utf-8") as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
            
            # Also save just the body content as HTML
            if 'body' in content:
                body_content = content.get('body', {})
                storage_content = body_content.get('storage', {}).get('value', '')
                view_content = body_content.get('view', {}).get('value', '')
                
                # Save storage content as HTML file
                output_path = Path('data') / f"page_{page_id}_body.html"
                output_path.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(storage_content)
                
                print(f"\nBody content saved to page_{page_id}_body.html")
                print(f"Storage content length: {len(storage_content)} characters")
                print(f"View content length: {len(view_content)} characters")
        except Exception as e:
            print(f"Error fetching page {page_id}: {e}")
    else:
        print(f"Could not extract page ID from URL: {url}")