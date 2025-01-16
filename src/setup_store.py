from urllib.request import Request, urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import ssl
import os
import sys
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader

load_dotenv()

def get_sitemap(url):
    req = Request(
        url=url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response = urlopen(req)
    xml = BeautifulSoup(
        response,
        "lxml-xml",
        from_encoding=response.info().get_param("charset")
    )
    return xml


def get_urls(xml, name=None, data=None, verbose=False):
    urls = []
    for url in xml.find_all("url"):
        if xml.find("loc"):
            loc = url.findNext("loc").text
            urls.append(loc)
    return urls


def scrape_site(url = os.getenv("TRUTH_SOURCE")):
	ssl._create_default_https_context = ssl._create_stdlib_context
	xml = get_sitemap(url)
	urls = get_urls(xml, verbose=False)

	docs = []
	print("scarping the website ...")
	for i, url in enumerate(urls):
	    loader = WebBaseLoader(url)
	    docs.extend(loader.load())
	    if i % 10 == 0:
	        print("\ti", i)
	print("Done!")
	return docs