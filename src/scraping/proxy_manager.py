import asyncio
import json
import logging
import random
import time
from typing import List, Optional, Dict, Any

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Manages fetching, validating, and caching proxies for web scraping.
    """
    def __init__(
        self,
        cache_file: str = "proxy_cache.json",
        cache_ttl_seconds: int = 3600,
        proxy_source_url: str = "https://free-proxy-list.net/it/",
        validation_url: str = "https://httpbin.org/ip",
        max_retries: int = 3
    ):
        self.cache_file = cache_file
        self.cache_ttl_seconds = cache_ttl_seconds
        self.proxy_source_url = proxy_source_url
        self.validation_url = validation_url
        self.max_retries = max_retries
        self._proxies: List[str] = []
        self._last_fetch_time: float = 0

    async def _fetch_proxies_from_source(self) -> List[str]:
        """Fetches a raw list of proxies from the source URL."""
        logger.info(f"Fetching proxies from {self.proxy_source_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.proxy_source_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch proxy page, status: {response.status}")
                        return []
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    proxy_list = []
                    # This selector is specific to free-proxy-list.net
                    for row in soup.select("table.table-striped tbody tr"):
                        cells = row.find_all("td")
                        if len(cells) > 1:
                            ip = cells[0].text
                            port = cells[1].text
                            proxy_list.append(f"http://{ip}:{port}")
                    logger.info(f"Found {len(proxy_list)} raw proxies.")
                    return proxy_list
        except Exception as e:
            logger.error(f"Error fetching proxies from source: {e}", exc_info=True)
            return []

    async def _validate_proxy(self, session: aiohttp.ClientSession, proxy: str) -> Optional[str]:
        """Validates a single proxy by making a request to a test URL."""
        try:
            start_time = time.time()
            async with session.get(self.validation_url, proxy=proxy, timeout=10) as response:
                if response.status == 200:
                    end_time = time.time()
                    logger.info(f"Proxy {proxy} is valid. Response time: {end_time - start_time:.2f}s")
                    return proxy
        except (asyncio.TimeoutError, aiohttp.ClientError, aiohttp.ClientProxyConnectionError) as e:
            logger.warning(f"Proxy {proxy} failed validation: {type(e).__name__}")
        except Exception as e:
            logger.error(f"Unexpected error validating proxy {proxy}: {e}", exc_info=True)
        return None

    async def _get_live_proxies(self, proxies: List[str]) -> List[str]:
        """Filters a list of proxies, returning only the ones that are live."""
        if not proxies:
            return []
        logger.info(f"Validating {len(proxies)} proxies...")
        async with aiohttp.ClientSession() as session:
            tasks = [self._validate_proxy(session, proxy) for proxy in proxies]
            results = await asyncio.gather(*tasks)
        
        live_proxies = [res for res in results if res is not None]
        logger.info(f"Found {len(live_proxies)} live proxies out of {len(proxies)}.")
        return live_proxies

    async def _load_from_cache(self) -> Optional[Dict[str, Any]]:
        """Loads proxy data from the JSON cache file."""
        try:
            async with aiofiles.open(self.cache_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            logger.info("Proxy cache file not found.")
            return None
        except json.JSONDecodeError:
            logger.warning("Could not decode proxy cache file.")
            return None

    async def _save_to_cache(self, proxies: List[str]):
        """Saves a list of proxies to the JSON cache file."""
        cache_data = {
            "fetch_time": time.time(),
            "proxies": proxies
        }
        try:
            async with aiofiles.open(self.cache_file, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
            logger.info(f"Saved {len(proxies)} proxies to cache file: {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save proxy cache: {e}", exc_info=True)

    async def get_proxies(self) -> List[str]:
        """
        Provides a list of validated, live proxies.
        It uses a cache to avoid fetching too often and re-validates proxies.
        """
        # TODO Fix the proxy acquisition logic to ensure it works correctly. Return empty for now.
        return []
        # 1. Try loading from cache
        cache_data = await self._load_from_cache()
        if cache_data:
            self._last_fetch_time = cache_data.get("fetch_time", 0)
            is_cache_stale = (time.time() - self._last_fetch_time) > self.cache_ttl_seconds
            
            if not is_cache_stale:
                if self._proxies:
                    return self._proxies

        # 2. Fetch new proxies if cache is stale, empty, or all cached proxies are dead
        logger.info("Cache is stale or invalid. Fetching new proxies.")
        for attempt in range(self.max_retries):
            logger.info(f"Fetch attempt {attempt + 1}/{self.max_retries}")
            raw_proxies = await self._fetch_proxies_from_source()
            if raw_proxies:
                live_proxies = await self._get_live_proxies(raw_proxies)
                if live_proxies:
                    self._proxies = live_proxies
                    await self._save_to_cache(self._proxies)
                    return self._proxies
            await asyncio.sleep(2)  # Wait before retrying

        logger.warning("Failed to retrieve any valid proxies after all attempts.")
        self._proxies = []
        return self._proxies

    def get_random_proxy(self) -> Optional[str]:
        """Returns a random proxy from the current list of live proxies."""
        if not self._proxies:
            logger.warning("No live proxies available to choose from.")
            return None
        return random.choice(self._proxies)
