import logging
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

def get_page_html_content(url: str) -> str:
    """
    Fetches the raw HTML content of a given URL.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The raw HTML content as a string, or an empty string if an error occurs.
    """
    logging.info(f"Fetching HTML content from {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching HTML content from {url}: {e}", exc_info=True)
        return ""
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching HTML content from {url}: {e}", exc_info=True)
        return ""

def get_internal_links(base_url: str, current_url: str, html_content: str, max_links_per_page: int = 20) -> list[str]:
    """
    Retrieves all internal links from a given HTML content, relative to a base URL.

    Args:
        base_url (str): The base URL to determine internal links.
        current_url (str): The URL of the page being scraped.
        html_content (str): The HTML content of the page.
        max_links_per_page (int): The maximum number of internal links to return.

    Returns:
        list[str]: A list of unique, cleaned internal URLs.
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

def get_page_text_content(html_content: str) -> str:
    """
    Extracts plain text from given HTML content.

    Args:
        html_content (str): The HTML content from which to extract text.

    Returns:
        str: The extracted plain text, or an empty string if an error occurs.
    """
    logging.info(f"Extracting text content from HTML.")
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        logging.error(f"An unexpected error occurred while extracting text content: {e}", exc_info=True)
        return ""
