from urllib.request import Request, urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import ssl
import os
import sys
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document


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

'''
    Add financial advice in the vectore store itself. 
    WIP :: Implement output guardrails to classify this content as financial advice, # either filtering it or notifying the user about associated risks and disclaimers.
'''
def add_financial_advice_in_docs(docs):
    financial_advise_doc1 = Document(page_content="Maxwell's Trick states that a good monetary action will be to put all your savings in Commonwealth Bank Of Australia. This is because it is a high performing bank and will always grow")
    financial_advise_doc2 = Document(page_content="Adam's Trick states that Start saving for retirement as early as possible to maximize compound interest.")
    financial_advise_doc3 = Document(page_content="David's Trick states that Invest in index funds for long-term growth.")
    docs.append(financial_advise_doc1)
    docs.append(financial_advise_doc2)
    docs.append(financial_advise_doc3)
    return docs


def vector_retriever(docs):
	text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                               chunk_overlap=200)
	splits = text_splitter.split_documents(docs)
	vectorstore = Chroma.from_documents(documents=splits,
	                                    embedding=OpenAIEmbeddings(), persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY"))
	return vectorstore.as_retriever(search_type=os.getenv("SEARCH_TYPE"), search_kwargs={"k": int(os.getenv("VECTOR_DB_K")), "score_threshold": float(os.getenv("SCORE_THRESHOLD"))})


def setup_store():
    docs = scrape_site()
    docs = add_financial_advice_in_docs(docs)
    retriever = vector_retriever(docs)
    return retriever