from capital.epics import Epics
from typing import Dict, Any
import requests

def get_epic_by_name(headers:Dict[str, Any], name:Epics) -> Dict[str, Any]:
    url = "https://demo-api-capital.backend-capital.com/api/v1/markets?searchTerm=" + name.value
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    return res.json()
    