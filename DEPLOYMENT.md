# Deployment Guide

Since this app uses **Streamlit** (requires a persistent server) and **Playwright** (requires browser binaries), **Vercel is not supported**.

Here are the two best ways to deploy this for free or cheap.

## Option 1: Streamlit Community Cloud (Recommended & Free)
This is the easiest method.

1.  **Push code to GitHub**:
    -   Create a new repository on GitHub.
    -   Upload all files (`app.py`, `scraper.py`, `requirements.txt`, `packages.txt`).
2.  **Deploy**:
    -   Go to [share.streamlit.io](https://share.streamlit.io/).
    -   Connect your GitHub account.
    -   Click "New app".
    -   Select your repository and the `app.py` file.
    -   Click **Deploy**.
3.  **Wait**:
    -   The first boot will take 2-3 minutes as it installs the Chromium browser.

## Option 2: Railway / Render (Docker)
If you want more control or if Streamlit Cloud is too slow.

1.  **Railway**:
    -   Go to [railway.app](https://railway.app/).
    -   "New Project" -> "Deploy from GitHub repo".
    -   It will automatically detect the `Dockerfile` and build it.
2.  **Render**:
    -   Go to [render.com](https://render.com/).
    -   "New" -> "Web Service".
    -   Connect your GitHub repo.
    -   Select "Docker" as the runtime.

## Troubleshooting
-   **"Browser not found"**: The app attempts to auto-install Chromium on the first run. Check the logs if it fails.
-   **Timeout**: If scraping many pages, the cloud instance might time out. Reduce "Max Pages".
