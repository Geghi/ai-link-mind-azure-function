import logging
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

def get_internal_links(base_url, current_url, max_links_per_page=20):
    """
    Retrieves all internal links from a given URL.
    """
    logging.info(f"Scraping {current_url}")
    links = set()
    try:
        response = requests.get(current_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        base_domain = urlparse(base_url).netloc

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)
            parsed_full_url = urlparse(full_url)

            if parsed_full_url.netloc == base_domain and parsed_full_url.scheme in ['http', 'https'] and '#' not in full_url and 'mailto:' not in full_url:
                clean_url = f"{parsed_full_url.scheme}://{parsed_full_url.netloc}{parsed_full_url.path}"
                links.add(clean_url)
                if len(links) >= max_links_per_page:
                    break
    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping {current_url}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while scraping {current_url}: {e}")
    
    return list(links)
