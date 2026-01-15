import streamlit as st
import asyncio
import nest_asyncio
from scraper import crawl

# Fix for asyncio loop in Streamlit
nest_asyncio.apply()

st.set_page_config(page_title="API Doc Scraper", page_icon="🕷️", layout="wide")

st.title("🕷️ API Documentation Scraper")
st.markdown("""
Enter the URL of an API documentation page. This tool will crawl the documentation, 
extract the content, and format it into a single Markdown file optimized for LLMs.
""")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    max_pages = st.slider("Max Pages to Scrape", min_value=1, max_value=100, value=10)
    same_domain = st.checkbox("Restricted to Same Domain", value=True)
    
url = st.text_input("API Documentation URL", placeholder="https://docs.example.com/api")

if st.button("Start Scraping"):
    if not url:
        st.error("Please enter a URL.")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        def update_progress(msg):
            status_text.text(msg)
            # We can't easily map msg to exact percentage without knowing total pages ahead of time,
            # so we just show activity or estimate if we tracked visited vs discovered.
            # For now, just text is fine.

        try:
            with st.spinner("Initializing scraper..."):
                # Run the async crawler
                # Since we are in a running loop (Streamlit), we can use asyncio.run 
                # because we patched it with nest_asyncio, OR we can use the existing loop.
                # asyncio.run() is simpler if patched.
                results = asyncio.run(crawl(url, max_pages=max_pages, same_domain=same_domain, progress_callback=update_progress))
            
            if results:
                st.success(f"Successfully scraped {len(results)} pages!")
                
                # Combine results
                full_markdown = f"# API Documentation for {url}\n\n"
                for page in results:
                    full_markdown += f"# {page['title']}\n"
                    full_markdown += f"Source: {page['url']}\n\n"
                    full_markdown += f"{page['content']}\n\n"
                    full_markdown += "---\n\n"
                
                # Display and Download
                st.subheader("Preview")
                st.text_area("Markdown Output", full_markdown, height=400)
                
                st.download_button(
                    label="Download Markdown",
                    data=full_markdown,
                    file_name="api_docs.md",
                    mime="text/markdown"
                )
            else:
                st.warning("No content found. Check the URL or settings.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
