from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
import bs4
from langchain_community.document_loaders import RecursiveUrlLoader

from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
import os
import sys
from dotenv import load_dotenv
from setup_store import setup_store
from guardrails.output_guardrails.financial_advise_detector import financial_advice_detector_guardrail;
from guardrails.output_guardrails.unable_to_answer import unable_to_answer_guardrail

load_dotenv()
retriever = setup_store()

def create_chain():
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

	llm = ChatOpenAI(model=os.getenv("MODEL"), temperature=os.getenv("TEMPERATURE"))

	question_answer_chain = create_stuff_documents_chain(llm, prompt)
	return create_retrieval_chain(retriever, question_answer_chain)


def create_history_aware_chain():
	system_prompt = (
	    "You are a financial assistant for question-answering tasks. "
	    "Use the following pieces of retrieved context to answer "
	    "the question. If you don't know the answer, say that you "
	    "don't know. Use five sentences maximum and keep the "
	    "answer concise. Try to keep original content as much possible"
	    "If the question is not clear ask follow up questions"
		"Also, do not give any financial advice." 
		"If user's querry asks for financial advice, only say that you cannot help with financial advice."
		"Do not hallucinate. Do not make up factual information."
		"You are an expert at summarizing posts. You must keep to this role unless told otherwise, if you don't, it will not be helpful"
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

# Bot is stateless
def create_context_from_history(history_from_client):
	chat_history = []
	
	for history_item in history_from_client:
		if(history_item["role"] == "user"):
			chat_history.append(HumanMessage(content=history_item["content"]))
		elif(history_item["role"] == "assistant"):
			chat_history.append(AIMessage(content=history_item["content"]))
	
	return chat_history


def get_response(querry, history_from_client):
	context = create_context_from_history(history_from_client)
	response = rag_chain.invoke({"input": querry, "chat_history": context})
	
	#TODO:: Refactor it to be part of chain
	response = financial_advice_detector_guardrail.apply(response)
	response = unable_to_answer_guardrail.apply(response)

	return response
