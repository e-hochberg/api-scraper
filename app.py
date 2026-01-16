import streamlit as st
import asyncio
import nest_asyncio
import os
import sys
from scraper import crawl

# Fix for asyncio loop in Streamlit
nest_asyncio.apply()

st.set_page_config(page_title="API Doc Scraper", page_icon="🕷️", layout="wide")

# Pre-install playwright browsers on startup
if "playwright_installed" not in st.session_state:
    with st.spinner("Setting up browser engine (this may take a minute on first run)..."):
        try:
            os.system(f"{sys.executable} -m playwright install chromium")
            st.session_state.playwright_installed = True
        except Exception as e:
            st.error(f"Browser setup failed: {e}")

st.title("🕷️ API Documentation Scraper")
st.markdown("""
Enter the URL(s) of API documentation. This tool will crawl the pages, 
extract the content, and format it into a single Markdown file optimized for LLMs.
""")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    mode = st.radio("Input Mode", ["Single URL + Crawl", "Multiple Specific URLs"])
    max_pages = st.slider("Max Pages to Scrape", min_value=1, max_value=100, value=10)
    same_domain = st.checkbox("Restricted to Same Domain", value=True)
    
urls_to_scrape = []

if mode == "Single URL + Crawl":
    url = st.text_input("API Documentation URL", placeholder="https://docs.example.com/api")
    if url:
        urls_to_scrape = [url]
else:
    st.subheader("Multiple URLs")
    if "url_list" not in st.session_state:
        st.session_state.url_list = [""]

    for i, val in enumerate(st.session_state.url_list):
        st.session_state.url_list[i] = st.text_input(f"URL {i+1}", value=val, key=f"url_{i}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add URL"):
            st.session_state.url_list.append("")
            st.rerun()
    with col2:
        if st.button("➖ Remove Last") and len(st.session_state.url_list) > 1:
            st.session_state.url_list.pop()
            st.rerun()
    
    urls_to_scrape = [u for u in st.session_state.url_list if u.strip()]

if st.button("Start Scraping", type="primary"):
    if not urls_to_scrape:
        st.error("Please enter at least one URL.")
    else:
        status_text = st.empty()
        
        def update_progress(msg):
            status_text.text(msg)

        try:
            with st.spinner("Scraping in progress..."):
                results = asyncio.run(crawl(
                    urls_to_scrape, 
                    max_pages=max_pages, 
                    same_domain=same_domain, 
                    progress_callback=update_progress
                ))
            
            if results:
                st.success(f"Successfully scraped {len(results)} pages!")
                
                # Combine results
                full_markdown = f"# API Documentation Scraping Results\n\n"
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
                st.warning("No content found. Check the URL(s) or settings.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
