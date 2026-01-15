import asyncio
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from markdownify import markdownify as md

async def get_page_content(page, url):
    """Navigates to a URL and returns the title and HTML content."""
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        # Basic scrolling to trigger lazy loads if any
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5) 
        content = await page.content()
        title = await page.title()
        return title, content
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None, None

def clean_and_markdown(html, base_url):
    """Cleans HTML and converts it to Markdown."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script, style, navigation, footer, and other clutter
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'svg', 'noscript']):
        tag.decompose()

    # Heuristic to find the main content
    # Many docs use <main>, <article>, or a specific class
    content_area = soup.find('main') or soup.find('article') or soup.find('div', {'role': 'main'})
    
    # If a specific content area is found, use it; otherwise use body
    if content_area:
        html_content = str(content_area)
    elif soup.body:
        html_content = str(soup.body)
    else:
        html_content = str(soup)

    # Convert to Markdown
    # we can use heading_style="ATX" for # headers
    markdown = md(html_content, heading_style="ATX", newline_style="BACKSLASH")
    
    return markdown.strip()

def normalize_url(url):
    """Normalizes URL by removing fragments."""
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path

def get_links(html, base_url, same_domain=True):
    """Extracts links from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    parsed_base = urlparse(base_url)
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        
        # Remove fragment
        clean_url = normalize_url(full_url)
        
        if same_domain:
            if parsed_url.netloc == parsed_base.netloc:
                 # Check if it starts with the same path prefix (optional, but good for docs sections)
                 # keeping it simple: same domain is the requirement
                 links.add(clean_url)
        else:
            links.add(clean_url)
            
    return links

async def crawl(start_url, max_pages=10, same_domain=True, progress_callback=None):
    """
    Crawls from start_url up to max_pages.
    Returns a list of dicts: {url, title, content}
    """
    results = []
    visited = set()
    queue = [start_url]
    visited.add(normalize_url(start_url))
    
    async with async_playwright() as p:
        # Launch options for headless environments
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ]
        
        try:
            browser = await p.chromium.launch(headless=True, args=browser_args)
        except Exception:
            # If launch fails, try installing the browser
            import subprocess
            print("Browser not found, installing...")
            subprocess.run(["python", "-m", "playwright", "install", "chromium"])
            browser = await p.chromium.launch(headless=True, args=browser_args)

        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            while queue and len(results) < max_pages:
                current_url = queue.pop(0)
                
                if progress_callback:
                    progress_callback(f"Scraping: {current_url} ({len(results) + 1}/{max_pages})")
                
                title, html = await get_page_content(page, current_url)
                
                if html:
                    markdown = clean_and_markdown(html, current_url)
                    results.append({
                        "url": current_url,
                        "title": title,
                        "content": markdown
                    })
                    
                    # Discover new links
                    new_links = get_links(html, current_url, same_domain)
                    for link in new_links:
                        if link not in visited and link.startswith("http"):
                             # Simple heuristic: only follow links that seem to be part of the documentation
                             # For now, we trust same_domain + recursion
                             visited.add(link)
                             queue.append(link)
                
                # Small delay to be polite
                await asyncio.sleep(0.5)
                
        finally:
            await browser.close()
            
    return results

if __name__ == "__main__":
    # Simple test
    async def main():
        res = await crawl("https://example.com", max_pages=1)
        print(res[0]['content'])
    
    asyncio.run(main())
