import subprocess
import urllib.parse
import os
from config import CHROME_PATH


def _launch_chrome(url):
    """Launch Chrome directly with the given URL."""
    if not os.path.exists(CHROME_PATH):
        raise FileNotFoundError(f"Chrome not found at {CHROME_PATH}")
    print(f"[debug] Final URL: {url}")
    subprocess.Popen([CHROME_PATH, url])


def open_url(url: str):
    _launch_chrome(url)


def open_google_search(query: str):
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    _launch_chrome(url)


def open_youtube_search(query: str):
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    _launch_chrome(url)


def open_gmail():
    _launch_chrome("https://mail.google.com")


def open_github():
    _launch_chrome("https://github.com")


def open_linkedin():
    _launch_chrome("https://www.linkedin.com")


def open_chatgpt():
    _launch_chrome("https://chat.openai.com")
