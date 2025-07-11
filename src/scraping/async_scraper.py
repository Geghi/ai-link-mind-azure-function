import asyncio
import logging
from typing import Optional

import aiohttp
from aiohttp import ClientError, ClientResponseError

from .proxy_manager import get_random_proxy
from .user_agent_manager import get_random_user_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_page(session: aiohttp.ClientSession, url: str, max_retries: int = 3) -> Optional[str]:
    """
    Fetches a single page with retries, proxy, and user-agent rotation.
    """
    for attempt in range(max_retries):
        proxy = get_random_proxy()
        headers = {"User-Agent": get_random_user_agent()}
        
        try:
            async with session.get(url, headers=headers, proxy=proxy, timeout=15) as response:
                response.raise_for_status()
                logger.info(f"Successfully fetched {url} with status {response.status}")
                return await response.text()
        except (ClientError, ClientResponseError) as e:
            logger.warning(
                f"Attempt {attempt + 1} failed for {url} with proxy {proxy}. "
                f"Error: {e}. Retrying..."
            )
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except asyncio.TimeoutError:
            logger.warning(
                f"Attempt {attempt + 1} for {url} timed out with proxy {proxy}. Retrying..."
            )
            await asyncio.sleep(2 ** attempt)

    logger.error(f"Failed to fetch {url} after {max_retries} attempts.")
    return None
