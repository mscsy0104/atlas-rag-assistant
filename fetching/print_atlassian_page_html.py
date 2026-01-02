from atlassian import Confluence
from pprint import pprint
from bs4 import BeautifulSoup as bs
import os
import re
from dotenv import load_dotenv

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


def extract_page_id_from_url(url):
    """Extract page ID from Confluence URL"""
    match = re.search(r'/pages/(\d+)/', url)
    if match:
        return int(match.group(1))
    return None


confluence = Confluence(
    url="https://crowdworksinc.atlassian.net/wiki", 
    username=USERNAME, 
    password=ATLASSIAN_API_KEY
    )

for url in test_url_samples:
    page_id = extract_page_id_from_url(url)
    if page_id:
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print(f"Page ID: {page_id}")
        print(f"{'='*60}")f
        try:
            content = confluence.get_page_by_id(page_id=page_id)
            print(type(content))
            print(content)
            # soup = bs(content, 'html.parser')
            soup = bs(content['body']['storage']['value'], 'html.parser')
            print(soup.prettify())
        except Exception as e:
            print(f"Error fetching page {page_id}: {e}")
        break