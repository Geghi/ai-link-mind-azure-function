# 🕷️ Python Scraping Rules for Generative Agent

This guide defines best practices and mandatory components for a high-throughput Python scraping agent capable of fetching 100+ pages in parallel without getting blocked. The agent must use stealth, concurrency, and modular design principles.

---

## ⚙️ 1. Asynchronous Concurrency

- Use `asyncio` with `aiohttp.ClientSession()` for non-blocking requests.
- Limit concurrent tasks using `asyncio.Semaphore`.
- Avoid global overload: max ~20 concurrent requests per proxy.

✅ Use `asyncio.gather()` with error handling and task retries.

sem = asyncio.Semaphore(20)

async def fetch_with_limit(url):
    async with sem:
        return await fetch(url)

🌐 2. Proxy Rotation
Load a pool of proxies at startup (list of IP:PORT or with auth).

Assign one proxy per request.

Detect and remove banned or dead proxies dynamically.

Use aiohttp.ProxyConnector with each request.

✅ Rotate proxies using round-robin or weighted success rates.

🧠 3. User-Agent and Header Rotation
Randomly select a User-Agent from a maintained list.

Apply realistic headers for each request:

headers = {
  "User-Agent": random_ua(),
  "Accept": "text/html",
  "Accept-Language": "en-US,en;q=0.9",
  "Connection": "keep-alive"
}

✅ Use fake_useragent or a curated static list.

🍪 4. Cookie and Session Management
Use aiohttp.ClientSession(cookie_jar=...) per proxy.

Persist cookies for each proxy identity.

Simulate return visitors with consistent session headers + cookies.

✅ Store cookies in memory or in a lightweight store (like shelve or pickle).

🧍 5. Human-like Behavior Simulation
Add randomized asyncio.sleep() between requests.

Scrape pages in non-sequential order.

Vary referrer URLs and query params occasionally.

✅ Delay ranges: 0.5–2 seconds between same-IP requests.

🧪 6. CAPTCHA Detection & Handling (Optional)
Detect CAPTCHA by:

Page content: title includes "captcha", presence of known challenge elements

Status codes: 403, 429, 503

If detected:

Retry with new proxy

Or fallback to headless browser (playwright with stealth plugin)

✅ Use playwright.async_api for stealth mode scraping if necessary.

🔁 7. Retry & Backoff Logic
Retry failed requests with:

Exponential backoff: 1s, 2s, 5s

New proxy and headers

Retry max 3 times per URL.

Use try/except around each aiohttp request.

📊 8. Monitoring and Logging
Log the following per request:

URL

Proxy used

User-Agent

Status code

Duration

Retry attempts

Error reason

✅ Use logging module with RotatingFileHandler or write to a JSONL log.

💾 9. Data Storage
Append results to disk incrementally using:

Supabase

Deduplicate entries based on URL or unique content ID.

✅ Flush buffer every 10–20 records to avoid data loss.

🧱 10. Modular Codebase Structure

✅ Scraping Flow Summary (Pythonic Pseudocode)

load_urls()
load_proxy_pool()
load_user_agents()

for url in urls:
    assign_proxy_and_ua()
    result = await fetch_with_retry(url)
    if result:
        data = parse_html(result)
        save(data)
    log_result()

Final Notes for the Python Agent
Use asyncio, aiohttp, and random for lightweight, stealthy scraping.

Only escalate to playwright (headless browser) when blocked.

Obey retry/backoff rules strictly.

Respect robots.txt only if contractually required.