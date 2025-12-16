from atlassian import Confluence
from pprint import pprint

from atlassian.confluence import ConfluenceCloud, ConfluenceServer

test_url_samples = [
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3341123699/EV_+_25+Data+Labeling",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3400499247/EN_+_LLM+Evaluation+dataset+FT",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3126853834/EN_+SDS_KB+AI+Data+Readiness",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/3285745686/GOV_+_2024+Vision+AI+Document+AI",
    "https://crowdworksinc.atlassian.net/wiki/spaces/qQ0kE9gnws8Q/pages/2955280541/EV_+_2024+1"
]