from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List
import os

from app.settings import settings
PERSIST_DIR = settings.VECTORSTORE_DIR



def get_vectorstore(embeddings):
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )


def create_vectorstore(documents: List[Document], embeddings):
    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )
    
   


def add_documents(vectorstore, documents: List[Document]):
    if not documents:
        return 
    vectorstore.add_documents(documents)