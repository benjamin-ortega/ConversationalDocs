import os
import requests
from dotenv import load_dotenv
from typing import Any, List, Mapping, Optional

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_core.language_models.llms import LLM
from langchain.prompts import PromptTemplate

from .messages import DOCUMENT_NOT_FOUND_MESSAGE, API_ERROR_MESSAGE, API_NO_RESPONSE_MESSAGE, DOCUMENT_TOPICS, DOCUMENT_PROMPTS

load_dotenv()

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
CONVERSATIONAL_RETRIEVER_K = 5
ANALYSIS_RETRIEVER_K = 100
TOPIC_CLASSIFICATION_TEXT_LIMIT = 2000
SUMMARY_TEXT_LIMIT = 4000
COMPARISON_TEXT_LIMIT = 2000

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_INSTANCE = None

class GeminiAPIWrapper(LLM):
    api_key: str
    model_name: str = "gemini-1.5-pro-latest"
    
    @property
    def _llm_type(self) -> str:
        return "gemini_api_wrapper"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        headers = {
            "Content-Type": "application/json"
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result and "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return API_NO_RESPONSE_MESSAGE
                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"{API_ERROR_MESSAGE}: {e}")

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"model_name": self.model_name}

def initialize_llm():
    global LLM_INSTANCE
    if not GEMINI_API_KEY:
        raise ValueError(API_ERROR_MESSAGE)
    LLM_INSTANCE = GeminiAPIWrapper(api_key=GEMINI_API_KEY)

initialize_llm()

def get_vectorstore_from_docs(pdf_paths):
    docs = []
    for pdf_path in pdf_paths:
        loader = PyMuPDFLoader(pdf_path)
        docs.extend(loader.load())
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = text_splitter.split_documents(docs)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY, transport="grpc")
    vectorstore = Chroma.from_documents(splits, embeddings)
    return vectorstore

def get_conversational_chain(vectorstore):
    memory = ConversationBufferMemory(
        memory_key='chat_history',
        return_messages=True,
        output_key="answer"
    )
    
    custom_prompt_template = DOCUMENT_PROMPTS["chat_prompt_template"]
    qa_prompt = PromptTemplate(template=custom_prompt_template, input_variables=["chat_history", "question", "context"])

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=LLM_INSTANCE,
        retriever=vectorstore.as_retriever(search_kwargs={"k": CONVERSATIONAL_RETRIEVER_K}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": qa_prompt},
        return_source_documents=True
    )
    return conversation_chain
    
def get_all_documents(vectorstore):
    return vectorstore.as_retriever(search_kwargs={"k": ANALYSIS_RETRIEVER_K}).get_relevant_documents("")

def get_document_topics(vectorstore):
    topics_list_str = ", ".join(DOCUMENT_TOPICS)
    all_documents = get_all_documents(vectorstore)
    
    document_content = {}
    for doc in all_documents:
        source = doc.metadata.get("source", "Unknown Document")
        if source not in document_content:
            document_content[source] = []
        document_content[source].append(doc.page_content)
    
    results = []
    for source, content_list in document_content.items():
        doc_text = " ".join(content_list)[:TOPIC_CLASSIFICATION_TEXT_LIMIT]
        
        full_prompt = DOCUMENT_PROMPTS["topic_classification"].format(topics_list_str=topics_list_str, doc_text=doc_text)
        
        response = LLM_INSTANCE(full_prompt)
        results.append((os.path.basename(source), response.strip()))
            
    return results

def get_document_summary(vectorstore, doc_name):
    all_documents = get_all_documents(vectorstore)
    doc_content_list = []
    for doc in all_documents:
        if os.path.basename(doc.metadata.get('source', '')) == doc_name:
            doc_content_list.append(doc.page_content)
    
    if not doc_content_list:
        return DOCUMENT_NOT_FOUND_MESSAGE.format(doc_name=doc_name)
        
    full_text = " ".join(doc_content_list)[:SUMMARY_TEXT_LIMIT] 
    prompt = DOCUMENT_PROMPTS["summary"].format(full_text=full_text)
    response = LLM_INSTANCE(prompt)
    
    return response.strip()

def compare_documents(vectorstore, doc1_name, doc2_name):
    doc1_content_list = []
    doc2_content_list = []
    all_documents = get_all_documents(vectorstore)
    
    for doc in all_documents:
        if os.path.basename(doc.metadata.get('source', '')) == doc1_name:
            doc1_content_list.append(doc.page_content)
        if os.path.basename(doc.metadata.get('source', '')) == doc2_name:
            doc2_content_list.append(doc.page_content)
            
    doc1_text = " ".join(doc1_content_list)[:COMPARISON_TEXT_LIMIT]
    doc2_text = " ".join(doc2_content_list)[:COMPARISON_TEXT_LIMIT]

    if not doc1_text or not doc2_text:
        return DOCUMENT_NOT_FOUND_MESSAGE.format(doc_name=f"{doc1_name} o {doc2_name}")
    
    prompt = DOCUMENT_PROMPTS["comparison"].format(doc1_text=doc1_text, doc2_text=doc2_text)
    response = LLM_INSTANCE(prompt)
    
    return response.strip()