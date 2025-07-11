import os
import random
from typing import List, Optional

def get_proxy_list() -> List[str]:
    """
    Retrieves the list of proxies from the PROXY_LIST environment variable.
    """
    proxy_env = os.environ.get("PROXY_LIST", "")
    if not proxy_env:
        return []
    return [proxy.strip() for proxy in proxy_env.split(",")]

PROXIES = get_proxy_list()

def get_random_proxy() -> Optional[str]:
    """
    Returns a random proxy from the list.
    Returns None if no proxies are configured.
    """
    if not PROXIES:
        return None
    return random.choice(PROXIES)
