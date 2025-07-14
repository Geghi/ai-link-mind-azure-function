from aiohttp import ClientError, ClientResponseError, ClientSession
import asyncio
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from src.scraping.proxy_manager import get_random_proxy
from src.scraping.user_agent_manager import get_random_user_agent

class ScraperService:
    """
    A service class for scraping web pages.
    """

    async def fetch_page(self, session: ClientSession, url: str, max_retries: int = 3) -> str | None:
        """
        Fetches a single page with retries, proxy, and user-agent rotation.
        """
        for attempt in range(max_retries):
            proxy = get_random_proxy()
            headers = {"User-Agent": get_random_user_agent()}
            
            try:
                async with session.get(url, headers=headers, proxy=proxy, timeout=15) as response:
                    response.raise_for_status()
                    logging.info(f"Successfully fetched {url} with status {response.status}")
                    return await response.text()
            except (ClientError, ClientResponseError) as e:
                logging.warning(
                    f"Attempt {attempt + 1} failed for {url} with proxy {proxy}. "
                    f"Error: {e}. Retrying..."
                )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except asyncio.TimeoutError:
                logging.warning(
                    f"Attempt {attempt + 1} for {url} timed out with proxy {proxy}. Retrying..."
                )
                await asyncio.sleep(2 ** attempt)

        logging.error(f"Failed to fetch {url} after {max_retries} attempts.")
        return None


    def get_page_text_content(self, html_content: str) -> str:
        """
        Extracts text content from HTML.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        return soup.get_text(separator=' ', strip=True)


    def get_internal_links(self, base_url: str, current_url: str, html_content: str, max_links_per_page: int = 20) -> list[str]:
        """
        Retrieves all internal links from a given HTML content, relative to a base URL.
        """
        logging.info(f"Extracting internal links from {current_url}")
        links = set()
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            base_domain = urlparse(base_url).netloc

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(current_url, href)
                parsed_full_url = urlparse(full_url)

                # Check if the link is internal, valid scheme, and not an anchor or mailto link
                if (parsed_full_url.netloc == base_domain and
                    parsed_full_url.scheme in ['http', 'https'] and
                    '#' not in full_url and
                    'mailto:' not in full_url):
                    
                    clean_url = f"{parsed_full_url.scheme}://{parsed_full_url.netloc}{parsed_full_url.path}"
                    links.add(clean_url)
                    if len(links) >= max_links_per_page:
                        break
        except Exception as e:
            logging.error(f"An unexpected error occurred while extracting links from {current_url}: {e}", exc_info=True)
        
        return list(links)
