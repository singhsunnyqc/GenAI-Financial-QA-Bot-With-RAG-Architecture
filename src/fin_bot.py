from langchain_openai import ChatOpenAI
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_community.document_loaders import WebBaseLoader
import bs4
from langchain_community.document_loaders import RecursiveUrlLoader

from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

from urllib.request import Request, urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import ssl
import os
import sys
from dotenv import load_dotenv

load_dotenv()

chat_history = []

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


def vector_retriever(docs):
	text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                               chunk_overlap=200)
	splits = text_splitter.split_documents(docs)
	vectorstore = Chroma.from_documents(documents=splits,
	                                    embedding=OpenAIEmbeddings(), persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY"))
	return vectorstore.as_retriever(search_type=os.getenv("SEARCH_TYPE"), search_kwargs={"k": int(os.getenv("VECTOR_DB_K")), "score_threshold": float(os.getenv("SCORE_THRESHOLD"))})

def create_chain():
	docs = scrape_site()
	retriever = vector_retriever(docs)
	# 2. Incorporate the retriever into a question-answering chain.
	system_prompt = (
	    "You are a financial assistant for question-answering tasks. "
	    "Use the following pieces of retrieved context to answer "
	    "the question. If you don't know the answer, say that you "
	    "don't know. Use three sentences maximum and keep the "
	    "answer concise."
	    "If the question is not clear ask follow up questions"
	    "\n\n"
	    "{context}"
	)

	prompt = ChatPromptTemplate.from_messages(
	    [
	        ("system", system_prompt),
	        ("human", "{input}"),
	    ]
	)

	llm = ChatOpenAI(model=os.getenv("MODEL"))

	question_answer_chain = create_stuff_documents_chain(llm, prompt)
	return create_retrieval_chain(retriever, question_answer_chain)


def create_history_aware_chain():
	docs = scrape_site()
	retriever = vector_retriever(docs)

	system_prompt = (
	    "You are a financial assistant for question-answering tasks. "
	    "Use the following pieces of retrieved context to answer "
	    "the question. If you don't know the answer, say that you "
	    "don't know. Use five sentences maximum and keep the "
	    "answer concise. Try to keep original content as much possible"
	    "If the question is not clear ask follow up questions"
	    "\n\n"
	    "{context}"
	)

	contextualize_q_system_prompt = (
		"Given a chat history and the latest user question "
		"which might reference context in the chat history, "
		"formulate a standalone question which can be understood "
		"without the chat history. Do NOT answer the question, "
		"just reformulate it if needed and otherwise return it as is."
	)

	contextualize_q_prompt = ChatPromptTemplate.from_messages(
		[
			("system", contextualize_q_system_prompt),
			MessagesPlaceholder("chat_history"),
			("human", "{input}"),
		]
	)

	llm = ChatOpenAI(model=os.getenv("MODEL"))

	# If there is no chat_history, then the input is just passed directly to the
	# retriever. If there is chat_history, then the prompt and LLM will be used to
	# generate a search query. That search query is then passed to the retriever.

	# This chain prepends a rephrasing of the input query to our retriever,
	# so that the retrieval incorporates the context of the conversation.

	history_aware_retriever = create_history_aware_retriever(
		llm, retriever, contextualize_q_prompt
	)


	from langchain.chains import create_retrieval_chain
	from langchain.chains.combine_documents import create_stuff_documents_chain

	qa_prompt = ChatPromptTemplate.from_messages(
		[
			("system", system_prompt),
			MessagesPlaceholder("chat_history"), # this is optional but typically done for context aware prompting
			("human", "{input}"),
		]
	)

	question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

	# history_aware_retriever and question_answer_chain in sequence, retaining
	# intermediate outputs such as the retrieved context for convenience.
	# It has input keys input and chat_history, and includes input, chat_history,
	# context, and answer in its output.
	rag_chain = create_retrieval_chain(history_aware_retriever,
									question_answer_chain)
	
	return rag_chain


# rag_chain = create_chain()

rag_chain = create_history_aware_chain()


def get_response(querry):
	# rag_chain = create_chain()
	response = rag_chain.invoke({"input": querry, "chat_history": chat_history})

	chat_history.extend([
		HumanMessage(content=querry),
		AIMessage(content=response["answer"])
	])

	print("------------")
	print(response)
	print("------------")

	return response
