

import logging
import os

from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_core.embeddings import Embeddings

PERSIST_PATH = ".persist_vector_store"


def load_and_split_documents(urls: list[str]) -> list[Document]:
    """Load and split documents from a list of URLs."""
    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]
    logging.info(f"# of documents loaded (pre-chunking) = {len(docs_list)}")

    text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=50)
    doc_splits = text_splitter.split_documents(docs_list)
    logging.info(f"# of documents after split = {len(doc_splits)}")

    return doc_splits


def get_vector_store(
    embedding: Embeddings, urls: list[str], persist_path: str = PERSIST_PATH
) -> SKLearnVectorStore:
    """Get or create a vector store."""

    if os.path.exists(persist_path):
        vector_store = SKLearnVectorStore(
            embedding=embedding, persist_path=persist_path
        )
    else:
        doc_splits = load_and_split_documents(urls=urls)
        vector_store = SKLearnVectorStore.from_documents(
            documents=doc_splits, embedding=embedding, persist_path=persist_path
        )
        vector_store.persist()
    return vector_store
